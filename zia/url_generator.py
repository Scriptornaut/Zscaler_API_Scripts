import random

# --- Configuration ---
NUM_URLS_TO_GENERATE = int(input("How many URLs do you want to generate?\n> "))
OUTPUT_FILENAME = "sample_urls.txt"

# --- Word lists to create realistic domains ---
ADJECTIVES = [
    "alpha", "apex", "arc", "atlas", "axiom", "blue", "bright", "core", "cosmic",
    "crystal", "delta", "dynamic", "echo", "elite", "epic", "ever", "fire",
    "flux", "fusion", "galaxy", "global", "golden", "horizon", "hyper", "icon",
    "ignite", "innova", "iron", "jet", "juniper", "keen", "kinetic", "level",
    "luna", "luxe", "matrix", "max", "meta", "momentum", "nexus", "nova",
    "omega", "omni", "onyx", "orbit", "origin", "paradigm", "peak", "pinnacle",
    "pioneer", "pivot", "prime", "pulse", "quantum", "quest", "radiant", "red",
    "rocket", "sapphire", "scope", "serene", "silver", "solar", "spark", "spectrum",
    "sphere", "stellar", "summit", "synergy", "terra", "titan", "triton",
    "true", "ultra", "unified", "vector", "velocity", "zenith", "zephyr"
]

NOUNS = [
    "analytics", "bridge", "capital", "cast", "centric", "chain", "cloud",
    "code", "coin", "comm", "connect", "core", "crest", "crew", "data", "deck",
    "desk", "dot", "drive", "edge", "engine", "financial", "flow", "force",
    "front", "grid", "group", "guard", "harbor", "health", "heavy", "hub",
    "industries", "interactive", "invest", "io", "key", "labs", "layer", "light",
    "link", "logic", "makers", "map", "media", "metrics", "micro", "mind",
    "mobile", "net", "node", "path", "point", "power", "protect", "protocol",
    "pulse", "quarter", "quest", "robotics", "round", "scale", "scan", "secure",
    "sense", "shield", "shift", "signal", "soft", "source", "space", "stack",
    "stone", "street", "strong", "sync", "systems", "tech", "trade", "trust",
    "valley", "ventures", "view", "vision", "wave", "works", "world", "yield"
]

TLDS = ["com", "net", "org", "io", "co", "ai", "tech", "cloud", "app"]

def generate_unique_urls(count):
    """Generates a set of unique URLs."""
    print(f"Generating {count} unique URLs...")
    generated_urls = set()
    while len(generated_urls) < count:
        adj = random.choice(ADJECTIVES)
        noun = random.choice(NOUNS)
        tld = random.choice(TLDS)
        # Combine them into a domain format
        url = f"{adj}-{noun}.{tld}"
        generated_urls.add(url)
    return list(generated_urls)

def save_urls_to_file(urls, filename):
    """Saves a list of URLs to a text file, one per line."""
    print(f"Writing {len(urls)} URLs to '{filename}'...")
    # Sort the list alphabetically for a clean output file
    urls.sort()
    with open(filename, "w") as f:
        for url in urls:
            f.write(f"{url}\n")
    print("Done!")

if __name__ == "__main__":
    unique_urls = generate_unique_urls(NUM_URLS_TO_GENERATE)
    save_urls_to_file(unique_urls, OUTPUT_FILENAME)
