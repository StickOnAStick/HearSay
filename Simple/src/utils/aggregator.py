from Simple.src.types.API import Cluster, Keyword, LLMOutput
from Simple.src.types.models import EmbeddingModel, ModelType
from Simple.src.types.client.clientstate import ReadOnlyClientState
from collections import defaultdict

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from loguru import logger
from pathlib import Path


import collections
import csv
import json
import os
import requests

class Aggregator:

    def __init__(self, global_state: ReadOnlyClientState):
        self.global_state = global_state
        self.package_dir = Path(__file__).parent.parent.parent # lol

    def aggregate(self) -> dict[str, list[Cluster]]:
        """
            Aggregates keyword data, saving results to a csv.
        """
        # frequencies: dict[str, int] keyword freq
        # For product in global_state.llm_output
            # For keyword in product
                # freq[keyword] += 1
                # compute weighted k-means

        # Find optimal cluster count for each product
        optimal_k: dict[str, int] = self.find_optimal_k_clusters(k_min=2)
        # Get product's keyword clusters
        cluster_keywords: dict[str, list[list[Keyword]]] = self.cluster_k_means(optimal_k=optimal_k)
        # Get labels for each product's cluster's keywords
        clusters: dict[str, list[Cluster]] = self.get_cluster_label(cluster_keywords)
        self.cluster_to_csv(clusters, self.global_state.keyword_source.stem.removesuffix("_keywords"))
        return clusters

    
    #Find optimal cluster value(k) to run kmeans using silhoutte score
    def find_optimal_k_clusters(self, k_min: int) -> dict[str, int]:

        # match product to it's optimal K
        res: dict[str, int] = {} 

        for product, llmOut in self.global_state.llm_output.items():
            embeddings: list[list[float]] = [keyword.embedding for keyword in llmOut.keywords]
            if len(embeddings) < k_min + 1:
                res[product] = 1
                continue
            
            max_silhouette_score = -1
            optimal_k: int = k_min
            k_max = len(llmOut.keywords)

            for k in range(k_min, k_max):
                kmeans = KMeans(n_clusters=k, n_init=10, random_state=0)
                kmeans.fit(embeddings)
                score = silhouette_score(embeddings, kmeans.labels_)

                if score > max_silhouette_score:
                    optimal_k, max_silhouette_score = k, score
            res[product] = optimal_k

        return res

    def cluster_k_means(self, optimal_k: dict[str, int]) -> dict[str, list[list[Keyword]]]:
        
        res: dict[str, list[list[Keyword]]] = {}

        for product, llmOut in self.global_state.llm_output.items():
            embeddings = [kw.embedding for kw in llmOut.keywords if kw.embedding]
            keywords = llmOut.keywords

            # Run kmeans on keyword embeddings
            kmeans = KMeans(n_clusters=optimal_k[product], init="k-means++", n_init=10, random_state=0)
            labels = kmeans.fit_predict(embeddings)

            # For each cluster found (clust 1, clust 2,...), match it's keyword (clust 1 keyword 0, clust 1 keyword 1, ...)
            clusters = [[] for _ in range(optimal_k[product])]
            for i, label in enumerate(labels):
                clusters[label].append(keywords[i])
            # Add found clusters to this product
            res[product] = clusters
        
        return res

    
    def get_cluster_label(self, prod_clusters: dict[str, list[list[Keyword]]]) -> list[Cluster]:
        
        res_clusters: dict[str, list[Cluster]] = defaultdict(list)

        for product_id, clusters in prod_clusters.items():
            
            for cluster in clusters:
                serialized_keywords = [kw.model_dump() for kw in cluster]
                # Get a label for the cluster's keywords
                response = requests.post(f"{self.global_state.end_point}/get_cluster_label/{ModelType.GPT4.value}", json=serialized_keywords)

                if not response.ok:
                    logger.error(f"Error: {response.status_code}, {response.json()}")
                    continue
                
                

                # Embed the label
                label = response.json().get("label")
                # API expects a LLMOutput object. Store the generated label here to get label embedding.
                dummy_input: LLMOutput = LLMOutput( 
                    product_id="",
                    keywords=[Keyword(product_id="", review_id="", keyword=label, sentiment=0.5)],
                    rating_count=0,
                    rating_sum=0,
                    summary=""
                )
                embedding_response = requests.post(f"{self.global_state.end_point}/get_embeddings/{EmbeddingModel.TEXT_SMALL3.value}", json=dummy_input.model_dump())
                label_embedding: LLMOutput = embedding_response.json().get('keywords', [])[0].get('embedding')
                res_cluster = Cluster(
                    product_id=product_id,
                    gen_keyword=label,
                    embedding=label_embedding,
                    sentiment_sum=sum(kw.sentiment for kw in cluster),
                    sentiment_count=len(cluster),
                    child_keywords=[kw.review_id for kw in cluster]
                )
                res_clusters[product_id].append(res_cluster)

        return res_clusters
    
    def cluster_to_csv(self, prod_clusters: dict[str, list[Cluster]], filename: str):
        with open(f"{self.package_dir}/data/output/{filename}-agg.csv", newline="", mode="w") as aggregator_csv:
            writer = csv.DictWriter(aggregator_csv, fieldnames=[
                'cluster_id', 'product_id', 'gen_keyword', 'sentiment_sum', 'sentiment_count', 'child_keywords', 'embedding'
            ])
            writer.writeheader()

            for prod_id, clusters in prod_clusters.items():
                for cluster in clusters:
                    writer.writerow({
                        'cluster_id': cluster.cluster_id,
                        'product_id': cluster.product_id,
                        'gen_keyword': cluster.gen_keyword,
                        'sentiment_sum': cluster.sentiment_sum,
                        'sentiment_count': cluster.sentiment_count,
                        'child_keywords': ','.join(cluster.child_keywords),  
                        'embedding': ",".join(map(str, cluster.embedding))
                    })

