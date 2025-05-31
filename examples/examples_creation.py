import json
import random
from pathlib import Path

def generate_topology(topology_num, nodes_range, links_range, ensure_valid_nodes=True):
    """
    Generate a network topology
    
    Args:
        topology_num (int): Topology identifier number
        nodes_range (tuple): (min_nodes, max_nodes) range for number of nodes
        links_range (tuple): (min_links, max_links) range for number of links
        ensure_valid_nodes (bool): If True, ensure all links connect existing nodes
    
    Returns:
        dict: Network topology in the specified JSON structure
    """
    
    # Generate random number of nodes within range
    min_nodes, max_nodes = nodes_range
    num_nodes = random.randint(min_nodes, max_nodes)
    
    # Generate nodes with names like "T001_Node001", "T001_Node002", etc.
    nodes = [f"T{topology_num:03d}_Node{i:03d}" for i in range(1, num_nodes + 1)]
    
    # Generate random number of links within range
    min_links, max_links = links_range
    num_links = random.randint(min_links, max_links)
    
    # If ensuring valid nodes, limit max links to avoid impossible scenarios
    if ensure_valid_nodes:
        # Maximum possible unique connections in a directed graph (avoiding self-loops)
        max_possible_links = num_nodes * (num_nodes - 1)
        num_links = min(num_links, max_possible_links)
    
    links = []
    existing_connections = set()
    
    for _ in range(num_links):
        attempts = 0
        
        while attempts < 100:  # Increased attempts for larger topologies
            if ensure_valid_nodes:
                # Select from existing nodes
                from_node = random.choice(nodes)
                to_node = random.choice(nodes)
                
                # Ensure we don't connect a node to itself
                if from_node != to_node:
                    connection_key = f"{from_node}-{to_node}"
                    
                    # Check for duplicate connections
                    if connection_key not in existing_connections:
                        existing_connections.add(connection_key)
                        
                        # Generate random latency between 1 and 200s
                        latency = random.randint(1, 10)
                        
                        links.append({
                            "from_node": from_node,
                            "to_node": to_node,
                            "latency": latency
                        })
                        break
            else:
                # Generate potentially invalid node names for testing
                from_node = f"T{topology_num:03d}_Node{random.randint(1, max_nodes + 50):03d}"
                to_node = f"T{topology_num:03d}_Node{random.randint(1, max_nodes + 50):03d}"
                
                if from_node != to_node:
                    connection_key = f"{from_node}-{to_node}"
                    
                    if connection_key not in existing_connections:
                        existing_connections.add(connection_key)
                        
                        latency = random.randint(1, 10)
                        
                        links.append({
                            "from_node": from_node,
                            "to_node": to_node,
                            "latency": latency
                        })
                        break
            
            attempts += 1
    
    # Generate random config values
    config = {
        "duration_sec": random.randint(10, 100),  # 30-900 seconds
        "packet_loss_percent": round(random.uniform(0, 15), 2),  # 0-15% with 2 decimal places
        "log_level": random.choice(["debug", "info", "warn", "error"])
    }
    
    return {
        "topology": {
            "nodes": nodes,
            "links": links
        },
        "config": config
    }

def generate_multiple_topologies(count, nodes_range, links_range, ensure_valid_nodes=True):
    """
    Generate multiple network topologies as an array
    
    Args:
        count (int): Number of topologies to generate
        nodes_range (tuple): (min_nodes, max_nodes) range for number of nodes
        links_range (tuple): (min_links, max_links) range for number of links
        ensure_valid_nodes (bool): If True, ensure all links connect existing nodes
    
    Returns:
        list: List of generated topologies
    """
    
    topologies = []
    
    for i in range(1, count + 1):
        topology = generate_topology(i, nodes_range, links_range, ensure_valid_nodes)
        topologies.append(topology)
    
    return topologies

def save_topologies_to_files():
    """Generate and save multiple topology sets to JSON files"""
    
    # Get the examples directory path
    examples_dir = Path(__file__).parent
    
    # Generate small topologies
    print("Generating small topologies...")
    small_topologies = generate_multiple_topologies(
        count=5,
        nodes_range=(5, 20),
        links_range=(3, 30),
        ensure_valid_nodes=True
    )
    
    # Save small topologies
    small_file = examples_dir / 'generated_topologies_small.json'
    with open(small_file, 'w') as f:
        json.dump(small_topologies, f, indent=2)
    print(f"✓ Saved: {small_file}")
    
    # Generate medium topologies
    print("Generating medium topologies...")
    medium_topologies = generate_multiple_topologies(
        count=3,
        nodes_range=(50, 150),
        links_range=(75, 300),
        ensure_valid_nodes=True
    )
    
    # Save medium topologies
    medium_file = examples_dir / 'generated_topologies_medium.json'
    with open(medium_file, 'w') as f:
        json.dump(medium_topologies, f, indent=2)
    print(f"✓ Saved: {medium_file}")
    
    # Generate large topologies
    print("Generating large topologies...")
    large_topologies = generate_multiple_topologies(
        count=2,
        nodes_range=(500, 1000),
        links_range=(1000, 2500),
        ensure_valid_nodes=True
    )
    
    # Save large topologies
    large_file = examples_dir / 'generated_topologies_large.json'
    with open(large_file, 'w') as f:
        json.dump(large_topologies, f, indent=2)
    print(f"✓ Saved: {large_file}")
    
    # Generate mixed size topologies in one file
    print("Generating mixed topologies...")
    mixed_topologies = []
    
    # Add various sized topologies to the mixed collection
    for i in range(1, 11):
        if i <= 3:  # Small
            topo = generate_topology(i, (10, 30), (15, 50), True)
        elif i <= 7:  # Medium
            topo = generate_topology(i, (100, 200), (150, 400), True)
        else:  # Large
            topo = generate_topology(i, (800, 1200), (1500, 3000), True)
        
        mixed_topologies.append(topo)
    
    # Save mixed topologies
    mixed_file = examples_dir / 'generated_topologies.json'
    with open(mixed_file, 'w') as f:
        json.dump(mixed_topologies, f, indent=2)
    print(f"✓ Saved: {mixed_file}")
    
    # Print statistics
    print("\n=== Generation Complete ===")
    print(f"Small topologies: {len(small_topologies)} topologies")
    print(f"Medium topologies: {len(medium_topologies)} topologies")
    print(f"Large topologies: {len(large_topologies)} topologies")
    print(f"Mixed topologies: {len(mixed_topologies)} topologies")
    
    # Detailed statistics
    print("\n=== Detailed Statistics ===")
    all_files = [
        ("Small", small_topologies),
        ("Medium", medium_topologies), 
        ("Large", large_topologies),
        ("Mixed", mixed_topologies)
    ]
    
    for file_type, data in all_files:
        print(f"\n{file_type} Topologies:")
        for i, topo_data in enumerate(data, 1):
            nodes_count = len(topo_data['topology']['nodes'])
            links_count = len(topo_data['topology']['links'])
            duration = topo_data['config']['duration_sec']
            packet_loss = topo_data['config']['packet_loss_percent']
            print(f"  Topology {i}: {nodes_count} nodes, {links_count} links, "
                  f"{duration}s duration, {packet_loss}% loss")

def main():
    save_topologies_to_files()

def generate_custom_topologies():
    """
    Function to generate custom topologies - modify parameters as needed
    """
    
    # Large topology example
    large_topology = generate_multiple_topologies(
        count=1,
        nodes_range=(800, 1200),
        links_range=(1500, 3000),
        ensure_valid_nodes=True
    )
    
    return large_topology

if __name__ == "__main__":
    main()  # Generate and save all topology files