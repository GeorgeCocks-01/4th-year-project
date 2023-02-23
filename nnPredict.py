import argparse
import numpy as np
from keras.models import load_model
from sklearn.metrics import accuracy_score
from nnTrain import getSplitData
from plotting import predictionsROCPlotter, shapPlotter

def main(args):
  for cut in ["2lep", "3lep"]: # Loop over the different selection cuts (2 and 3 lepton)

    x_train, x_test, y_train, y_test = getSplitData(cut, 0)

    # Load the model
    if args.inputModel:
      model = load_model("nnModels/" + args.inputModel + cut + ".h5")
    else:
      model = load_model("nnModels/trained" + cut + ".h5")

    if args.verbose:
      print(model.summary())

    # Predict the labels
    pred = model.predict(x_test)
    y_pred = np.rint(pred).astype(int)

    # Get the accuracy
    print("Accuracy for " + cut + " cut: " + str(accuracy_score(y_test, y_pred)))

    # Plot graphs
    predictionsROCPlotter(model, pred, y_test, y_train, x_train, cut)

    if args.shap:
      # Plot the SHAP values
      shapPlotter(model, x_train, cut)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description = "Predict and plot graphs using an imported neural network")
  parser.add_argument("-i", "--input", type = str, dest = "inputModel", default = None,
    help = "Input file name of the neural network model (without 2/3lep).")
  parser.add_argument("-s", "--SHAP", action = "store_true", dest = "shap", default = None,
    help = "Whether to plot the SHAP values or not.")
  parser.add_argument("-v", "--verbose", action = "store_true", dest = "verbose", default = None,
    help = "Whether to print out the model summary or not.")
  args = parser.parse_args()

  main(args)
