import hashlib
import json

def normalize_links(links):
    # Remove keys you want to ignore and sort for consistency
    return sorted([
        {
            "from_node": link["from_node"],
            "to_node": link["to_node"],
            "latency": link["latency"]
        } for link in links
    ], key=lambda l: (l["from_node"], l["to_node"], l["latency"]))

def get_fingerprint(doc):
    simplified = {
        "nodes": sorted(doc["nodes"]),
        "links": normalize_links(doc["links"]),
        "config": doc["config"]
    }
    doc_str = json.dumps(simplified, sort_keys=True)
    return hashlib.sha256(doc_str.encode()).hexdigest()
