from Simple.src.types.API import Cluster, Keyword, LLMOutput
from Simple.src.types.models import EmbeddingModel, ModelType
from Simple.src.types.client.clientstate import ReadOnlyClientState


from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from loguru import logger


import collections
import csv
import json
import os
import requests

class Aggregator:

    def __init__(self, global_state: ReadOnlyClientState, keywords_csv: str, output_file: str):
        self.global_state = global_state
        self.package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.keywords_csv = f"{self.package_dir}/data/output/{keywords_csv}.csv"
        self.output_file = output_file

    def aggregate(self):
        """
            Aggregates keyword data, saving results to a csv.
        """
        keywords: list[Keyword] = self.get_keywords()
        optimal_k: int = self.find_optimal_k_clusters(keywords=keywords, k_min=1, k_max=len(keywords))
        cluster_keywords: list[list[Keyword]] = self.cluster_k_means(k=optimal_k, keywords=keywords)
        clusters: list[Cluster] = self.get_cluster_label(cluster_keywords)
        self.cluster_to_csv(clusters, filename=self.output_file)

    def get_keywords(self) -> list[Keyword]:
        keywords: list[Keyword] = []
        with open(self.keywords_csv, mode='r') as keywords_csv:
            reader = csv.DictReader(keywords_csv)

            for row in reader:
                keyword: Keyword = Keyword(
                    product_id = row['product_id'],
                    keyword = row['keyword'],
                    sentiment = row['sentiment'],
                    embedding = json.loads(row['embedding'])
                )
                keywords.append(keyword)
        return keywords
    
    #Find optimal cluster value(k) to run kmeans using silhoutte score
    def find_optimal_k_clusters(self, keywords: list[Keyword], k_min: int, k_max: int) -> int:
        embeddings: list[list[float]]= [keyword.embedding for keyword in keywords]
        optimal_k: int = k_min
        max_silhouette_score: float = -1

        #Finds k with highest silhouette score
        for k in range(k_min, k_max+1):
            kmeans = KMeans(n_clusters=k, n_init=10, random_state=0)
            labels = kmeans.fit(embeddings)
            score = silhouette_score(embeddings, labels)

            if score>max_silhouette_score:
                optimal_k, max_silhouette_score = k, score

        return optimal_k

    def cluster_k_means(self, k: int, keywords: list[Keyword]) -> list[Cluster]:
        embeddings: list[list[float]]= [keyword.embedding for keyword in keywords]

        #Run kmeans on keyword embeddings
        kmeans = KMeans(n_clusters=k, init='k-means++', n_init=10, random_state=0)
        kmeans.fit(embeddings)

        cluster_labels = kmeans.labels_
        clusters = collections.defaultdict(list)

        #Add each keyword to its assigned cluster
        for idx, cluster in cluster_labels:
            clusters[cluster].append(keywords[idx])

        #return a list of Cluster objects with it's list of keywords
        return clusters.values()
    
    def get_cluster_label(self, clusters: list[list[Keyword]]) -> list[Cluster]:
        
        res_clusters = []
        for cluster_keywords in clusters:
            serialized_keywords = [keywords.model_dump() for keywords in cluster_keywords]
            response = requests.post(f"{self.global_state.end_point}/get_cluster_label/{ModelType.GPT4.value}", json=serialized_keywords)
            
            if response.status_code == 200:
                label = response.json().get("label")  
                dummy_output = LLMOutput(
                    keywords = [label],
                    rating = 0.0,
                    summary = "",
                )
                embedding_response = requests.get(f"{self.global_state.end_point}/get_embeddings/{EmbeddingModel.TEXT_SMALL3.value}", json=dummy_output.model_dump())
                
                try:
                    keyword_embeddings = embedding_response.get('keywords', [])
                    if len(keyword_embeddings) != len(dummy_output.keywords):
                        logger.exception(f"Mismatch between keywords and embeddings count in response for llmOutput")
                        continue
                    
                    res_cluster = Cluster(
                        product_id = cluster_keywords[0].product_id,
                        gen_keyword = label,
                        embedding = keyword_embeddings[0].get("embedding"),
                        sentiment_sum = sum(kw.sentiment for kw in cluster_keywords),
                        sentiment_count = sum(kw.frequency for kw in cluster_keywords),
                        child_keywords = [kw.review_id for kw in cluster_keywords]
                    )
                    res_clusters.append(res_cluster)
                except KeyError as e:
                    logger.exception(f"Missing expected key in the api response {e}")
                
            else:
                logger.exception(f"Error: {response.status_code}, {response.json()}")

        return res_clusters
    
    def cluster_to_csv(self, clusters: list[Cluster], filename: str):
        with open(f"{self.package_dir}/data/output/agg-{filename}.csv", newline="", mode="w") as aggregator_csv:
            writer = csv.DictWriter(aggregator_csv, fieldnames=[
                'product_id', 'gen_keyword', 'embedding', 'total_sentiment', 'num_occur', 'original_keywords'
            ])
            writer.writeheader()

            for cluster in clusters:
                writer.writerow({
                    'product_id': cluster.product_id,
                    'gen_keyword': cluster.gen_keyword,
                    'embedding': ",".join(map(str, cluster.embedding)),  
                    'total_sentiment': cluster.total_sentiment,
                    'num_occur': cluster.num_occur,
                    'original_keywords': ','.join(cluster.original_keywords)  
                })

