import random
import json # Using JSON is clean and easy to parse

def generate_random_hamiltonian_path(rows, cols):
    """
    Generates a random Hamiltonian path on a grid using a randomized
    backtracking algorithm. A Hamiltonian path visits every node (clock)
    exactly once.

    Args:
        rows (int): The number of rows in the grid.
        cols (int): The number of columns in the grid.

    Returns:
        list[int] or None: A list of clock indices representing the path,
                           or None if a path couldn't be found (unlikely for a grid).
    """
    total_nodes = rows * cols
    path = []
    visited = [False] * total_nodes

    def _get_neighbors(node):
        """Calculates valid neighbors (up, down, left, right) for a given node index."""
        r, c = divmod(node, cols)
        neighbors = []
        if r > 0: neighbors.append(node - cols)       # Up
        if r < rows - 1: neighbors.append(node + cols) # Down
        if c > 0: neighbors.append(node - 1)         # Left
        if c < cols - 1: neighbors.append(node + 1)   # Right
        return neighbors

    def _find_path_from(node):
        """Recursive helper to find a path starting from the current node."""
        path.append(node)
        visited[node] = True

        # Base case: If the path is complete, we're done.
        if len(path) == total_nodes:
            return True

        neighbors = _get_neighbors(node)
        random.shuffle(neighbors) # This is the key to getting a random path

        for neighbor in neighbors:
            if not visited[neighbor]:
                if _find_path_from(neighbor):
                    return True # Path found, propagate success

        # Backtrack if no unvisited neighbor led to a solution
        visited[node] = False
        path.pop()
        return False

    # Start the search from a random node
    start_node = random.randint(0, total_nodes - 1)
    if _find_path_from(start_node):
        return path
    else:
        # This should theoretically not happen on a standard grid
        # unless it's disconnected or 1x1.
        return None

def create_path_file(num_paths, rows, cols, filename="hamiltonian_paths.json"):
    """Generates a specified number of unique paths and saves them to a file."""
    all_paths = set() # Use a set to store paths as tuples to ensure uniqueness
    print(f"Generating {num_paths} unique paths for a {rows}x{cols} grid...")

    while len(all_paths) < num_paths:
        path = generate_random_hamiltonian_path(rows, cols)
        if path:
            all_paths.add(tuple(path)) # Add tuple to set for uniqueness check
            print(f"  Found path {len(all_paths)}/{num_paths}")

    # Convert set of tuples back to a list of lists for saving
    paths_to_save = [list(p) for p in all_paths]

    with open(filename, 'w') as f:
        json.dump(paths_to_save, f)
    
    print(f"\nSuccessfully saved {len(paths_to_save)} paths to '{filename}'.")

# --- Run the generator ---
if __name__ == "__main__":
    # For your 3x8 clock grid
    GRID_ROWS = 3
    GRID_COLS = 8
    
    # Generate 50 unique paths and save them
    create_path_file(num_paths=100, rows=GRID_ROWS, cols=GRID_COLS)