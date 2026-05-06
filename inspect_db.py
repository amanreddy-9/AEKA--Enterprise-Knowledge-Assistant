import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("aeka_knowledge")

print(f"Total chunks: {collection.count()}")
print()

results = collection.get(include=["documents", "metadatas"])

# Show unique documents
files = {}
for meta in results["metadatas"]:
    f = meta.get("file", "unknown")
    files[f] = files.get(f, 0) + 1

print("=== Documents in Knowledge Base ===")
for filename, count in files.items():
    print(f"  {filename} → {count} chunks")

print()
print("=== Sample Chunks (first 3) ===")
for i in range(min(3, len(results["documents"]))):
    print(f"\n--- Chunk {i} ---")
    print(f"File: {results['metadatas'][i]['file']}")
    print(f"Text: {results['documents'][i][:200]}...")