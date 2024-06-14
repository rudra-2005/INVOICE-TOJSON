from openai import OpenAI

client=OpenAI(api_key="YOUR_API_KEY")

status=client.fine_tuning.jobs.retrieve("job_id")

checkpoint=client.fine_tuning.jobs.checkpoints.list("job_id")
lists=client.models.list()
# print(status)
print(checkpoint)
fine_tuned_model=lists.data[-1].id
#print(fine_tuned_model)