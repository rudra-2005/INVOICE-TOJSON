from openai import OpenAI
       
client = OpenAI( api_key = "YOUR_API_KEY")

file = client.files.create(
    
  file = open(r"C:\Users\RUDRA\Desktop\INVOICE PROCESSING\Training_file", "rb"),

  purpose="fine-tune"
)

fine_tuning_job=client.fine_tuning.jobs.create(
  training_file=file.id,
 model="gpt-3.5-turbo", 
  hyperparameters={
    "n_epochs":1
  }
 ) 
print(fine_tuning_job)

