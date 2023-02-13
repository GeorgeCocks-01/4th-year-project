import shap
import matplotlib
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

matplotlib.use("SVG") # Use SVG for matplotlib

def predictionsROCPlotter(model, pred, y_test, y_train, X_train, cut):
  ### Plots Predictions and ROC curve ###
  fpr, tpr, thresholds = roc_curve(y_test, pred) # Calculate the ROC curve
  rocArea = auc(fpr, tpr) # Calculate the area under the ROC curve

  # Plot the ROC curve
  plt.figure(figsize = (8, 6))
  plt.plot([0, 1], [0, 1], linestyle = "--", color = "black")
  plt.plot(fpr, tpr)
  plt.title(cut + " ROC curve")
  plt.ylabel("True positive rate")
  plt.xlabel("False positive rate")
  plt.legend(["Baseline", "ROC curve (area = %0.3f)" % rocArea], loc = 'lower right')
  plt.savefig("nnPlots/roc" + cut + ".png")
  plt.clf()

  signalPredictionTest = pred[y_test == 1]
  backgroundPredictionTest = pred[y_test == 0]
  # verbose = 0 means no output
  signalPredictionTrain = model.predict(X_train, verbose = 0)[y_train == 1]
  backgroundPredictionTrain = model.predict(X_train, verbose = 0)[y_train == 0]

  # Plot the predictions
  plt.figure(figsize = (8, 6))
  for i, j in zip((signalPredictionTest, backgroundPredictionTest, signalPredictionTrain, backgroundPredictionTrain),
    ("Signal Test", "Background Test", "Signal Train", "Background Train")):
    plt.hist(i, bins = 50, range = (0, 1), label = j, histtype= "step", density = True)
  plt.title(cut + " Prediction (testing)")
  plt.ylabel("Number of events")
  plt.xlabel("Prediction")
  plt.legend(loc = 'upper center', ncol = 2)
  plt.savefig("nnPlots/predictions" + cut + ".png")
  plt.clf()

def trainingPlotter(modelFit, cut):
  ### Plots the loss and accuracy for each epoch of training ###
  for i in ("loss", "accuracy"):
    plt.figure(figsize = (8, 6))
    plt.plot(modelFit.history[i])
    plt.plot(modelFit.history["val_" + i])
    plt.title(cut + " Model" + i.capitalize())
    plt.ylabel(i.capitalize())
    plt.xlabel("Epoch")
    plt.legend(['Train', 'Test'], loc = 'upper left')
    plt.savefig("nnPlots/" + i + cut + ".png")
    plt.clf()

def shapPlotter(model, X_train, features, cut):
  ### Plots the SHAP values ###
  explainer = shap.Explainer(model, X_train, feature_names = features)
  shap_values = explainer(X_train)

  shap.plots.bar(shap_values, show = False)
  plt.savefig("nnPlots/shapBar" + cut + ".png")
  plt.clf()
