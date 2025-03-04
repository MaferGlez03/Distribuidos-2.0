class Node:
    def __init__(self, value):
        self.value = value
        self.next = None
        self.prev = None

class FlexibleQueue:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def push_front(self, value):
        new_node = Node(value)
        if not self.head:
            self.head = self.tail = new_node
        else:
            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node
        self.size += 1

    def push_back(self, value):
        new_node = Node(value)
        if not self.tail:
            self.head = self.tail = new_node
        else:
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node
        self.size += 1

    def push_at(self, value, index):
        if index <= 0:
            self.push_front(value)
        elif index >= self.size:
            self.push_back(value)
        else:
            new_node = Node(value)
            current = self.head
            for _ in range(index - 1):
                current = current.next
            new_node.next = current.next
            new_node.prev = current
            if current.next:
                current.next.prev = new_node
            current.next = new_node
            self.size += 1

    def pop_front(self):
        if not self.head:
            return None
        value = self.head.value
        self.head = self.head.next
        if self.head:
            self.head.prev = None
        else:
            self.tail = None
        self.size -= 1
        return value

    def pop_back(self):
        if not self.tail:
            return None
        value = self.tail.value
        self.tail = self.tail.prev
        if self.tail:
            self.tail.next = None
        else:
            self.head = None
        self.size -= 1
        return value

    def pop_at(self, index):
        if index <= 0:
            return self.pop_front()
        elif index >= self.size - 1:
            return self.pop_back()
        else:
            current = self.head
            for _ in range(index):
                current = current.next
            value = current.value
            current.prev.next = current.next
            if current.next:
                current.next.prev = current.prev
            self.size -= 1
            return value

    def display(self):
        current = self.head
        values = []
        while current:
            values.append(current.value)
            current = current.next
        print("Queue:", values)

# Ejemplo de uso
queue = FlexibleQueue()
queue.push_back(10)
queue.push_front(5)
queue.push_at(7, 1)
queue.display()
queue.pop_at(1)
queue.display()
