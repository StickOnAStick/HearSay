
import collections
import csv
import json
from Simple.types.API import Cluster, Keyword
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

class Aggregator:

    def __init__(self, keywords_csv: str):
        self.keywords_csv = keywords_csv

    def aggregate(self):
        keywords: list[Keyword] = self.get_keywords()
        optimal_k: int = self.find_optimal_k_clusters(keywords=keywords, k_min=1, k_max=len(keywords))
        clusters: list[Cluster] = self.cluster_k_means(k=optimal_k, keywords=keywords)

        pass

    def get_keywords(self) -> list[Keyword]:
        keywords: list[Keyword] = []
        with open(self.keywords_csv, mode='r') as keywords_csv:
            reader = csv.DictReader(keywords_csv)

            for row in reader:
                keyword: Keyword = Keyword(
                    keyword = row['keyword'],
                    frequency = row['frequency'],
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
        return [Cluster(keywords=cluster_keywords) for cluster_keywords in clusters.values()]
    
    
