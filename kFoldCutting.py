from array import array
import uproot
import ROOT
import numpy as np
from selectionPlots import findAllFilesInPath

def main():
  # Create a canvas
  ROOT.gROOT.LoadMacro('../atlasrootstyle/AtlasStyle.C')
  ROOT.gROOT.LoadMacro('../atlasrootstyle/AtlasUtils.C')
  ROOT.gROOT.SetBatch(ROOT.kTRUE)
  ROOT.SetAtlasStyle()
  canvas = ROOT.TCanvas("c", "c", 800, 600)
  canvas.cd()

  # Get the samples from the outputNTuples folder, store them in a dictionary with 1 for signal and 0 for background
  sample_names = findAllFilesInPath("*.root", "nTupleGroups/")

  # Thresholds for 2lep, 3lep cuts
  thresholds = (0.5, 0.5)

  for cut, threshold in zip(("2lep", "3lep"), thresholds):
    # dictionary of the delta phi ll arrays for each sample
    delta_phi_ll_dict = {
      "signal": np.array([]),
      "llll": np.array([]),
      "other di-boson": np.array([]),
      "jets": np.array([])
    }
    weight_dict = dict.fromkeys(delta_phi_ll_dict, np.array([]))
    predictions_dict = dict.fromkeys(delta_phi_ll_dict, np.array([]))

    # Get the delta phi ll arrays for each sample
    for sample in sample_names:
      match sample:
        case "nTupleGroups/signalGroup.root":
          key = "signal"
        case "nTupleGroups/llllGroup.root":
          key = "llll"
        case "nTupleGroups/backgroundGroup.root":
          key = "other di-boson"
        case "nTupleGroups/jetsGroup.root":
          key = "jets"
      with uproot.open(sample + ":nominal" + cut) as tree:
        delta_phi_ll_dict[key] = tree["deltaPhill"].array(library = "np")
        weight_dict[key] = tree["weight"].array(library = "np")

    # Get predictions and group number from kFold.py ntuples
    with uproot.open("kFoldNTuples/predictions.root:nominal" + cut) as f:
      prediction = f["prediction"].array(library = "np")
      group_number = f["group"].array(library = "np")

    # Sort predictions into groups
    for i, key in enumerate(predictions_dict):
      predictions_dict[key] = prediction[group_number == i]

    # Cut delta phi ll arrays using threshold
    for key in delta_phi_ll_dict:
      # print(len(delta_phi_ll_dict[key]))
      # print(len(predictions_dict[key]))
      delta_phi_ll_dict[key] = delta_phi_ll_dict[key][predictions_dict[key] > threshold]
      weight_dict[key] = weight_dict[key][predictions_dict[key] > threshold]

    print("Number of events after cut for " + cut + ":", sum([len(delta_phi_ll_dict[key]) for key in delta_phi_ll_dict]))

    # Generate histogram for output
    delta_phi_ll_histograms =  {
      "signal": ROOT.TH1D("signal" + cut, "delta_phi_ll" + cut + ";Delta Phi(Rad);Normalised Counts", 50, -4, 4),
      "llll": ROOT.TH1D("llll" + cut, "delta_phi_ll" + cut + ";Delta Phi(Rad);Normalised Counts", 50, -4, 4),
      "other di-boson": ROOT.TH1D("di-boson" + cut, "delta_phi_ll" + cut + ";Delta Phi(Rad);Normalised Counts", 50, -4, 4),
      "jets": ROOT.TH1D("jets" + cut, "delta_phi_ll" + cut + ";Delta Phi(Rad);Normalised Counts", 50, -4, 4)
    }

    # Fill histogram with delta phi ll values
    for key in delta_phi_ll_dict:
      arr = array('d', delta_phi_ll_dict[key])
      weight_arr = array('d', weight_dict[key])
      delta_phi_ll_histograms[key].FillN(len(arr), arr, weight_arr)

    ### PLOTTING ###
    # Create a legend
    leg = ROOT.TLegend(0.7,0.6,0.8,0.85)
    leg.SetBorderSize(0)
    leg.SetTextSize(0.03)
    leg.SetEntrySeparation(0.001)

    colours = [ROOT.kRed, ROOT.kBlack, ROOT.kBlue, ROOT.kGreen]
    maximum = -999
    for i, key in enumerate(delta_phi_ll_histograms):
      hist = delta_phi_ll_histograms[key]
      hist.SetLineColor(colours[i])

      # Normalise the histograms
      hist.Scale(1./hist.Integral())

      # Get the maximum value of the histograms
      if hist.GetMaximum() > maximum and key != "jets":
        maximum = hist.GetMaximum()

    for i, key in enumerate(delta_phi_ll_histograms):
      hist = delta_phi_ll_histograms[key]
      if i == 0:
        hist.SetMaximum(maximum * 1.2)
        hist.Draw("hist")
      else:
        hist.Draw("histSAME")

      leg.AddEntry(hist, key, "l")

    leg.Draw('SAME')

    # Save the canvas
    canvas.SaveAs("signedDeltaPhill/" + cut + ".pdf")
    canvas.Clear()
    ### END OF PLOTTING ###

if __name__ == "__main__":
  main()
