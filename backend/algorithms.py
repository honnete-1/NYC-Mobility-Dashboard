# I created a  Custom Min-Heap implementation for top-K busiest zones
# I did it because it was part of the technical requirement for manual algorithmic logic without libraries.

class MinHeap:
    def __init__(self, max_size):
        """Initializes the min-heap with a fixed maximum size (K)."""
        self.max_size = max_size
        self.heap = []  

    def parent(self, i):
        return (i - 1) // 2

    def left_child(self, i):
        return 2 * i + 1

    def right_child(self, i):
        return 2 * i + 2

    def sift_up(self, i):
        """Restores heap property upwards from index i."""
        while i > 0 and self.heap[i][0] < self.heap[self.parent(i)][0]:
            parent_idx = self.parent(i)
            self.heap[i], self.heap[parent_idx] = self.heap[parent_idx], self.heap[i]
            i = parent_idx

    def sift_down(self, i):
        """Restores heap property downwards from index i."""
        min_idx = i
        left = self.left_child(i)
        right = self.right_child(i)
        
        if left < len(self.heap) and self.heap[left][0] < self.heap[min_idx][0]:
            min_idx = left
        if right < len(self.heap) and self.heap[right][0] < self.heap[min_idx][0]:
            min_idx = right
            
        if i != min_idx:
            self.heap[i], self.heap[min_idx] = self.heap[min_idx], self.heap[i]
            self.sift_down(min_idx)

    def push(self, element):
        """Pushes an element onto the heap. 
        If the heap size exceeds K, the root is replaced if the new element is larger."""
        if len(self.heap) < self.max_size:
            self.heap.append(element)
            self.sift_up(len(self.heap) - 1)
        else:
            if element[0] > self.heap[0][0]:
                self.heap[0] = element
                self.sift_down(0)

    def get_sorted_elements(self):
        """Returns all heap elements sorted in descending order (largest first)."""
        sorted_list = []
        temp_heap = list(self.heap)
        while self.heap:
            self.heap[0], self.heap[-1] = self.heap[-1], self.heap[0]
            val = self.heap.pop()
            self.sift_down(0)
            sorted_list.append(val)
        self.heap = temp_heap
        return sorted_list[::-1]
