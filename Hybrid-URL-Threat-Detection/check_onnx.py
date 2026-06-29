import onnxruntime as ort

session = ort.InferenceSession(
    "app/model/hybrid_model.onnx"
)

print("INPUTS:")
for inp in session.get_inputs():
    print(inp.name, inp.shape, inp.type)

print("\nOUTPUTS:")
for out in session.get_outputs():
    print(out.name, out.shape, out.type)