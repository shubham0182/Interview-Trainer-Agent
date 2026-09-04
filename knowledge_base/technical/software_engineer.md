---
role: software_engineer
type: technical
difficulty: medium
---

# Software Engineer — Technical Interview Questions

## Data Structures & Algorithms

### Arrays and Strings
- Explain the difference between an array and a linked list. When would you use each?
- How would you find duplicates in an array in O(n) time?
- Describe the two-pointer technique and give an example problem it solves.

### Trees and Graphs
- Explain BFS vs DFS. When is each approach preferable?
- What is a balanced binary search tree? Why does balance matter for performance?
- How would you detect a cycle in a directed graph?

### Dynamic Programming
- What is memoization? How does it differ from tabulation?
- Describe the general approach to solving a DP problem.
- Explain the concept of overlapping subproblems with an example.

## System Design

### Fundamentals
- What is horizontal vs vertical scaling? When would you choose each?
- Explain the CAP theorem. What trade-offs does it describe?
- What is a load balancer and why is it important in distributed systems?

### Databases
- When would you choose a relational database over a NoSQL database?
- Explain database indexing. What are the trade-offs of adding indexes?
- What is database sharding and when is it needed?

### APIs
- What is REST? What are its core constraints?
- Explain idempotency in HTTP methods. Which methods are idempotent?
- How would you version a REST API?

## Object-Oriented Programming

- Explain the four pillars of OOP: encapsulation, abstraction, inheritance, polymorphism.
- What is the difference between composition and inheritance? When should you prefer composition?
- Describe the SOLID principles. Give an example of violating the Single Responsibility Principle.

## Model Answers

**Q: Explain the difference between an array and a linked list.**

An array stores elements in contiguous memory locations, enabling O(1) random access by index. A linked list stores elements in nodes where each node holds data and a pointer to the next node; access requires O(n) traversal but insertion/deletion at a known position is O(1). Use arrays for frequent reads by index; use linked lists for frequent insertions/deletions at arbitrary positions.

**Q: What is horizontal vs vertical scaling?**

Vertical scaling (scale up) means adding more resources (CPU, RAM) to an existing machine. It has a hardware ceiling and creates a single point of failure. Horizontal scaling (scale out) means adding more machines and distributing load across them. It is more resilient and practically unbounded, but requires applications to be stateless and adds coordination complexity (load balancing, distributed state management).
