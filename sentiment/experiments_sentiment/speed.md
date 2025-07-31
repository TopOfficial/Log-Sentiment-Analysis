# 50 samples
### CoT Prompt

![alt text](image.png)
- ~1100 seconds
- ~1000 seconds

### Normal Prompt
![alt text](image-2.png)
- ~820 seconds
- ~900 seconds

### CoT Prompt with batching (Send multiple log lines in each request) (10 samples each)
- Better Accuracy than Normal Prompt

![alt text](image-1.png)
- ~970 seconds

### CoT Prompt with batching (multiple log lines in one prompt)
- Lower accuracy and shouldn't be use.
