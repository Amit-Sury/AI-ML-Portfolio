# Introduction
This project implements a **Convolutional Neural Network (CNN)** to classify images of animals. It leverages:
- **Jupyter Notebook** and **AWS SageMaker Script Mode** for custom training, packaging dependencies, and handling deployment.  
- **AWS SageMaker** for model inference, enabling scalable and managed predictions.

---

# Steps to Deploy this Model in AWS Sagemaker

- **Step 1:** Create a bucket in S3 and upload the images in following folder structure
 ```bash
  dataset/
  ├── train/
  │   ├── dog/
  │   ├── elephant/
  │   └── horse/
  └── validation/
      ├── dog/
      ├── elephant/
      └── horse/
 ```
💡 *Note: The number of classes is not hard-coded. We can add more classes aka folders (e.g., ``` /lion ```) with images 
in both ```train``` and ```validation``` folders, the model will detect it as a new class and automatically adapt to include it during
training. Make sure each class has a reasonable number of images otherwise the dataset will be imbalanced.* 

- **Step 2:** Update the **cnn-tensorflow-sagemaker.ipynb** notebook with actual bucket name in **2<sup>nd</sup> cell**. Also update the name of
  test image files in **9<sup>th</sup> cell** while calling ```predict_image()``` function.   
- **Step 3:** Go to **AWS SageMaker** and start a notebook instance.
- **Step 4:** Once started, open the notebook instance which will open jupyter notebook instance in a separate window.  
- **Step 5:** Upload **“cnn-tensorflow-sagemaker.ipynb”**, **“train-cnn.py”** to the notebook instance. These will be used for training
  the CNN model.
- **Step 6:** Also upload sample test images like ```“dog.jpeg”```, ```“elephant.jpeg”```, ```“horse.jpeg”```
  (these will be used to make prediction). Double check that the name of these test image files are updated in **9<sup>th</sup> cell** of notebook
  while calling ```predict_image()``` as per step 2 above. 
- **Step 7:** Open **“cnn-tensorflow-sagemaker.ipynb”** and run the Jupyter Notebook. Use ```conda-python3``` as kernel.
- **Step 8:** Once done remember to **delete the endpoint** and **stop/delete the notebook instance** to avoid unnecessary charges.
  (Double-check the Endpoints, Notebook page in **AWS Sagemaker** to confirm deletion.)
