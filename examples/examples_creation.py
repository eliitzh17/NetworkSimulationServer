import json
import random
import string
import argparse
from typing import List, Dict, Any

def generate_node_name(existing_nodes: List[str], name_length: int = 1) -> str:
    """Generate a unique node name that doesn't exist in the list of nodes."""
    while True:
        if name_length == 1:
            # Single letter nodes (A, B, C, etc.)
            node_name = random.choice(string.ascii_uppercase)
        else:
            # Node names with prefix like N1, N2, etc.
            prefix = random.choice(string.ascii_uppercase)
            suffix = str(random.randint(1, 99))
            node_name = f"{prefix}{suffix}"
        
        if node_name not in existing_nodes:
            return node_name

def generate_topology(min_nodes: int = 20, max_nodes: int = 100) -> Dict[str, Any]:
    """Generate a random network topology with nodes and links."""
    num_nodes = random.randint(min_nodes, max_nodes)
    
    # Generate nodes
    nodes = []
    for _ in range(num_nodes):
        # Decide whether to use single-letter or prefix-number style
        name_style = random.choice([1, 2])
        node_name = generate_node_name(nodes, name_style)
        nodes.append(node_name)
    
    # Generate links
    links = []
    
    # Ensure connectivity by creating a path through all nodes
    for i in range(num_nodes - 1):
        from_node = nodes[i]
        to_node = nodes[i + 1]
        latency = random.randint(1, 30)
        links.append({
            "from_node": from_node,
            "to_node": to_node,
            "latency": latency
        })
    
    # Add some random additional links for more complex topologies
    num_additional_links = random.randint(0, num_nodes)
    for _ in range(num_additional_links):
        from_idx = random.randint(0, num_nodes - 1)
        to_idx = random.randint(0, num_nodes - 1)
        
        # Avoid self-loops and duplicate links
        if from_idx != to_idx:
            from_node = nodes[from_idx]
            to_node = nodes[to_idx]
            
            # Check if this link already exists
            link_exists = any(
                link["from_node"] == from_node and link["to_node"] == to_node
                for link in links
            )
            
            if not link_exists:
                latency = random.randint(1, 30)
                links.append({
                    "from_node": from_node,
                    "to_node": to_node,
                    "latency": latency
                })
    
    return {
        "topology": {
            "nodes": nodes,
            "links": links
        }
    }

def generate_config() -> Dict[str, Any]:
    """Generate a random configuration."""
    duration_options = [30, 60, 90, 120, 180, 240, 300]
    log_levels = ["debug", "info", "warning", "error"]
    
    return {
        "duration_sec": random.choice(duration_options),
        "packet_loss_percent": round(random.uniform(0, 5.0), 1),
        "log_level": random.choice(log_levels)
    }

def generate_network_config() -> Dict[str, Any]:
    """Generate a complete network configuration."""
    topology = generate_topology()
    config = generate_config()
    
    topology["config"] = config
    return topology

def main():
    """Main function to generate and output network configurations."""
    parser = argparse.ArgumentParser(description='Generate network topology JSON configurations')
    parser.add_argument('-n', '--num-configs', type=int, default=10, 
                        help='Number of configurations to generate (default: 10)')
    parser.add_argument('-o', '--output', type=str, default='network_configs.json',
                        help='Output file path (default: network_configs.json)')
    parser.add_argument('--pretty', action='store_true',
                        help='Format JSON with indentation for readability')
    args = parser.parse_args()
    
    # Generate configurations
    configurations = []
    for _ in range(args.num_configs):
        config = generate_network_config()
        configurations.append(config)
    
    # Write to file
    indent = 2 if args.pretty else None
    with open(args.output, 'w') as f:
        json.dump(configurations, f, indent=indent)
    
    print(f"Generated {args.num_configs} network configurations and saved to {args.output}")
    
    # Print sample of output
    sample_size = min(3, args.num_configs)
    print(f"\nSample of {sample_size} configurations:")
    for i, config in enumerate(configurations[:sample_size]):
        num_nodes = len(config["topology"]["nodes"])
        num_links = len(config["topology"]["links"])
        print(f"Configuration {i+1}: {num_nodes} nodes, {num_links} links")
    print(json.dumps(configurations[:sample_size], indent=2))

if __name__ == "__main__":
    main()