---
role: devops_engineer
type: technical
difficulty: medium
---

# DevOps Engineer — Technical Interview Questions

## CI/CD

- Explain the difference between Continuous Integration, Continuous Delivery, and Continuous Deployment.
- What does a typical CI/CD pipeline look like? What stages does it include?
- How would you design a zero-downtime deployment strategy?
- What is blue-green deployment vs canary deployment?

## Containerization and Orchestration

- What is the difference between a container and a virtual machine?
- Explain the key concepts in Docker: image, container, Dockerfile, registry.
- What problem does Kubernetes solve? Describe pods, services, and deployments.
- How does Kubernetes handle service discovery and load balancing?

## Infrastructure as Code

- What is Infrastructure as Code (IaC)? What problems does it solve?
- Compare Terraform and Ansible. When would you use each?
- What is idempotency in the context of IaC tools?

## Monitoring and Observability

- What are the three pillars of observability?
- Explain the difference between monitoring and alerting.
- What metrics would you track for a web application?

## Networking and Security

- Explain the difference between TCP and UDP. When is UDP preferred?
- What is a reverse proxy? How does it differ from a forward proxy?
- How would you secure secrets in a CI/CD pipeline?

## Model Answers

**Q: What is blue-green deployment?**

Blue-green deployment maintains two identical production environments: blue (current) and green (new). Traffic is routed to blue while green is deployed and tested. When green is verified, traffic is switched instantly. Rollback is a traffic switch back to blue. This achieves zero downtime and instant rollback but requires double the infrastructure during the transition.

**Q: What are the three pillars of observability?**

Logs (timestamped records of discrete events), Metrics (numeric measurements aggregated over time — CPU, latency, error rate), and Traces (end-to-end records of a request path through distributed services). Together they provide a complete view: metrics alert you that something is wrong, logs tell you what happened, traces show you where in the system it happened.
