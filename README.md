# VibeCoding — AI-Driven Cloud-Native Development with AWS Kiro & Edge Delta

This repository showcases my project from the **AWS × Edge Delta “Prototype to Production” Hackathon**, where I explored how **AI-powered development environments** like **AWS Kiro** can accelerate the entire development lifecycle — from build → deploy → monitor — all through conversational prompts.

---

## Project: Flappy Kiro

**Flappy Kiro** is a containerized arcade-style game featuring a ghost character navigating through wall gaps.  
It demonstrates how an agentic AI IDE (Kiro) can create, containerize, and deploy applications on **AWS EKS** with full observability using **Edge Delta AI Teammates**.

---

## Tech Stack

| Layer | Technologies |
|-------|---------------|
| Frontend | HTML5 Canvas, JavaScript, CSS3, Nginx, OpenTelemetry Browser SDK |
| Backend | Python Flask REST API, Gunicorn WSGI, JSON leaderboard, OpenTelemetry Tracing |
| Infrastructure | AWS EKS Cluster, ECR Registry, Application Load Balancer (ALB) |
| Monitoring & Observability | Edge Delta AI Teammates, AWS X-Ray, CloudWatch Logs |
| Containerization | Docker, Kubernetes manifests, automated build & push scripts |

---

## Features

- AI-assisted build and deployment via AWS Kiro IDE  
- Fully containerized frontend and backend microservices  
- Integrated OpenTelemetry for distributed tracing  
- Real-time monitoring and log analytics through Edge Delta  
- Scalable EKS cluster deployment using Infrastructure-as-Code  
- Global leaderboard with username validation and persistent storage  

---

## Architecture Overview
User → ALB → Frontend Service → Frontend Pod → Backend Service → Backend Pod → Data Storage


---

## Key Learnings

- How AI can act as a DevOps teammate  
- End-to-end observability using OpenTelemetry  
- Deploying microservices with AWS EKS and Edge Delta  
- AI-driven Infrastructure-as-Code via Kiro prompts  

---

## Acknowledgments

Huge thanks to the **AWS**, **Edge Delta**, and **VibeCoding** teams for organizing the hackathon and creating such a hands-on learning experience.  
Special appreciation to everyone I met during the event — your collaboration and creativity made this project even better.  

---

## Connect

**Author:** Harika Gummadi  
**LinkedIn:** [https://www.linkedin.com/in/harikagummadi](https://www.linkedin.com/in/harikagummadi)  
**Email:** harikagummadi582@gmail.com  

---

### Tags
AWS • Edge Delta • VibeCoding • Kiro • Hackathon • Cloud Computing • EKS • AI in DevOps • Kubernetes • OpenTelemetry • Python • Flask • Nginx • DevOps • AI Engineering • Seattle Tech • Innovation


