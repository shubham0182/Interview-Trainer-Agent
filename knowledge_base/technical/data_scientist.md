---
role: data_scientist
type: technical
difficulty: medium
---

# Data Scientist — Technical Interview Questions

## Statistics and Probability

- What is the difference between Type I and Type II errors?
- Explain the Central Limit Theorem and its significance in data science.
- What is p-value? How do you interpret a p-value of 0.03?
- Explain the bias-variance trade-off. How do you balance it?

## Machine Learning

### Supervised Learning
- What is the difference between classification and regression?
- Explain gradient descent. What are learning rate trade-offs?
- How does regularization (L1 vs L2) help prevent overfitting?
- What metrics would you use to evaluate a classification model on an imbalanced dataset?

### Unsupervised Learning
- How does K-means clustering work? What are its limitations?
- Explain Principal Component Analysis (PCA). When would you use it?

### Model Evaluation
- What is cross-validation? Why is it better than a single train/test split?
- Explain precision, recall, and F1-score with a real-world example.
- What is AUC-ROC? How do you interpret an AUC of 0.5?

## Deep Learning
- What is the vanishing gradient problem? How does it affect training?
- Explain dropout regularization. How does it reduce overfitting?
- What is transfer learning? Give an example use case.

## Data Engineering
- How would you handle missing data in a dataset?
- Explain feature engineering. Give an example of creating a useful derived feature.
- What is the difference between normalization and standardization?

## Model Answers

**Q: What is the bias-variance trade-off?**

Bias is the error from incorrect model assumptions — a high-bias model underfits, missing patterns in the data. Variance is the error from sensitivity to noise in the training data — a high-variance model overfits, memorizing training data but failing on new data. The trade-off means reducing bias typically increases variance and vice versa. The goal is to find the complexity level that minimizes total error (bias² + variance + irreducible noise).

**Q: Explain precision and recall.**

Precision = TP / (TP + FP) — of all positive predictions, how many were correct. Recall = TP / (TP + FN) — of all actual positives, how many did we catch. High precision is important when false positives are costly (e.g. spam detection). High recall is important when false negatives are costly (e.g. cancer screening). F1-score is the harmonic mean, useful when you need a single metric balancing both.
