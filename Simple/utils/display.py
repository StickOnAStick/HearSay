import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
import csv

# Currently does not account for duplicated keywords, and has inconsistent patterning

#product = [product_id, sentiment]
products=[]
#aggregate = [product_id, aggregate_id, sentiment, keywords]
aggregates=[]
#keyword = [keyword, sentiment]
keywords=[]

# Temp return values
def read_product_csv():
	try:
		with open('../data/output/Products.csv', newline='') as csvfile:
			reader = csv.reader(csvfile)
			next(reader)
			for line in reader:
				products.append([line[0], line[2]])
	except FileNotFoundError:
		print("No Products.csv file found")
		exit()

# Temp return values
def read_aggregate_csv():
	try:
		with open('../data/output/Aggregated.csv', newline='') as csvfile:
			reader = csv.reader(csvfile)
			next(reader)
			for line in reader:
				aggregates.append([line[0], line[1], line[3], line[5].split(',')])
	except FileNotFoundError:
		print("No Aggregated.csv file found")
		exit()

# Temp return values
def read_keywords_csv():
	try:
		with open('../data/output/Keywords.csv', newline='') as csvfile:
			reader = csv.reader(csvfile)
			next(reader)
			for line in reader:
				keywords.append([line[1], line[3]])
	except FileNotFoundError:
		print("No Keywords.csv file found")
		exit()

def display():
	# Call Read Commands
	read_product_csv()
	read_aggregate_csv()
	read_keywords_csv()

	# Start Diagram & Color Map
	diagram = nx.Graph()
	color_map = []

	#For each product, add product_node
	for product in products:

		# Create basic product node and then attach aggregates
		product_node = product[0] + "\n" + product[1]
		diagram.add_node(product_node)
		color_map.append('skyblue')
		
		for aggregate in aggregates:
			# Only include if aggregate is part of product
			if (aggregate[0] == product[0]):

				aggregate_node = aggregate[1] + "\n" + aggregate[2]
				diagram.add_node(aggregate_node)
				diagram.add_edge(product_node, aggregate_node)

				# Assign color based on sentiment
				if(float(aggregate[2]) > 0):
					color_map.append('mediumseagreen')
				else:
					color_map.append('tomato')

				# Keywords in aggregate
				for keyword in keywords:
					if(keyword[0] in aggregate[3]):

						# Create Keyword node and assign sentiment color
						keyword_node = keyword[0] + "\n" + keyword[1]
						diagram.add_node(keyword_node)
						diagram.add_edge(aggregate_node, keyword_node)

						# Define color for higher or lower sentiment
						if(float(keyword[1]) > 0):
							color_map.append('springgreen')
						else:
							color_map.append('coral')

	# Define layout, window size, and draw graph
	pos = nx.spring_layout(diagram, k=0.20)
	plt.figure(figsize=(12,8))
	nx.draw(diagram, pos, with_labels=True, node_size=3000, node_color=color_map, font_size=10, font_weight='bold', edge_color='gray')
	
	plt.title("Sentiment Display", fontsize=16)
	plt.axis('equal')
	plt.show()

display()
