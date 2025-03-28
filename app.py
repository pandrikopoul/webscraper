  import gradio as gr
  import pandas as pd

  def filter_records(records, gender):
      return records[records["gender"] == gender]

  with gr.Blocks() as demo:
      with gr.Row():
          with gr.Column():
              data_input = gr.Dataframe(
                  headers=["name", "age", "gender"],
                  datatype=["str", "number", "str"],
                  row_count=5,
                  col_count=(3, "fixed"),
                  interactive=True
              )
              gender_input = gr.Dropdown(["M", "F", "O"])
              submit_button = gr.Button("Submit")
          with gr.Column():
              data_output = gr.Dataframe(
                  headers=["name", "age", "gender"],
                  datatype=["str", "number", "str"],
                  col_count=(3, "fixed"),
                  interactive=True
              )

      submit_button.click(filter_records, inputs=[data_input, gender_input], outputs=data_output)

  demo.launch(server_name="0.0.0.0", server_port=7860)
