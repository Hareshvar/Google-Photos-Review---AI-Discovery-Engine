from backend.api.router import get_overview

res = get_overview()
stats = res.get("stats", {})
print("--- OVERVIEW STATS ---")
print("Collected:", stats.get("collected"))
print("Cleaned:", stats.get("cleaned"))
print("Relevant:", stats.get("relevant"))
print("Vague Memory Count:", stats.get("vague_memory_count"))
print("Search Failures Count:", stats.get("search_failures_count"))

relevant = stats.get("relevant", 1)
sf_count = stats.get("search_failures_count", 0)
vm_count = stats.get("vague_memory_count", 0)

print(f"Search Failures %: {(sf_count / relevant) * 100:.1f}%")
print(f"Vague Memory %: {(vm_count / relevant) * 100:.1f}%")
