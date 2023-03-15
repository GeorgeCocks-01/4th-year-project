from math import sqrt
import ctypes
from ROOT import *
from selectionPlots import findAllFilesInPath
from kFoldCutting import significance_calc

gROOT.LoadMacro('../atlasrootstyle/AtlasStyle.C')
gROOT.LoadMacro('../atlasrootstyle/AtlasUtils.C')
gROOT.SetBatch(kTRUE)
SetAtlasStyle()

canv = TCanvas('c','c',1300,900)
canv.cd()
colorList = [kBlack,kRed,kBlue,kGreen,kViolet,kMagenta,kAzure,kOrange,kYellow,kMagenta+3,kCyan,kYellow+2]

folder = "outputRoot/"

zJetsSamples = []
zJetsSamples.extend(findAllFilesInPath("*Zee*.root", folder + "/"))
zJetsSamples.extend(findAllFilesInPath("*Zmumu*.root", folder + "/"))
zJetsSamples.extend(findAllFilesInPath("*Ztt*.root", folder + "/"))

samples = (('llll', (folder + '/llll-weighted.root', folder + '/llll_lowMllPtComplement-weighted.root'), kMagenta),
      ('other di-boson', (folder + '/ZqqZll-weighted.root',
        folder + '/lllv-weighted.root',
        folder + '/lllv_lowMllPtComplement-weighted.root',
        folder + '/llvv-weighted.root',
        folder + '/llvv_lowMllPtComplement-weighted.root',
        folder + '/WqqZll-weighted.root',
        folder + '/ttH-weighted.root'), kBlue),
      ('Jets', zJetsSamples, kGreen),
      ('signal', (folder + '/ZHlltt-weighted.root', folder + '/ggZH-weighted.root'), kRed))

varList = ["tau_pt_sum", "Z_lepton_mass_sum", "met_pt", "delta_R_ll", "delta_R_tt",
           "delta_Eta_ll", "delta_Eta_tt", "delta_R_tt_ll", "n_jets", "delta_Phi_ll",
           "delta_Phi_tt", "delta_Phi_ll_tt", "mmc_mass"]

varXAxis = {
    "tau_pt_sum": "p_{T}^{#tau_{sum}} (GeV)",
    "Z_lepton_mass_sum": "M_{ll} (GeV)",
    "met_pt": "E_{T}^{miss} (GeV)",
    "delta_R_ll": "#Delta R_{ll}",
    "delta_R_tt": "#Delta R_{#tau#tau}",
    "delta_Eta_ll": "#Delta #eta_{ll}",
    "delta_Eta_tt": "#Delta #eta_{#tau#tau}",
    "delta_R_tt_ll": "#Delta R_{#tau#tau,ll}",
    "n_jets": "Number of jets",
    "delta_Phi_ll": "#Delta#phi_{ll} (Rad)",
    "delta_Phi_tt": "#Delta#phi_{#tau#tau} (Rad)",
    "delta_Phi_ll_tt": "#Delta#phi_{ll,#tau#tau} (Rad)",
    "mmc_mass": "MMC mass (GeV)"
}

# Clear plottingYields.txt
open("plottingYields.txt", "w").close()

for cut in ["2_lep_", "3_lep_"]: # Loop over the different selection cuts (2 and 3 lepton)
  cutYields = {samples[0][0]: None, samples[1][0]: None, samples[2][0]: None, samples[3][0]: None}
  cutErrors = {samples[0][0]: None, samples[1][0]: None, samples[2][0]: None, samples[3][0]: None}
  for variable in varList: # Loop over the variables
    var = cut + variable
    leg = TLegend(0.37, 0.5, 0.73, 0.73) #0.5,0.7,0.7,0.85
    leg.SetBorderSize(0)
    leg.SetTextSize(0.03)
    leg.SetEntrySeparation(0.001)
    leg.SetTextSize(0.055)

    counter = 0
    histos=[]
    legnames=[]
    maximum = -999.
    stackedHisto = THStack()
    for i in range(len(samples)): # Loop over the sample groups
      sample = samples[i]

      for j in range(len(sample[1])): # Loop over the files in the sample group
        infile = TFile.Open(sample[1][j],"READ")
        histo = infile.Get(var)
        histo.SetDirectory(0)
        if j == 0:
          histos.append(histo)
        else:
          histos[i].Add(histo)
        infile.Close()

      histos[i].SetLineWidth(3)
      histos[i].SetMarkerColor(sample[2])
      histos[i].SetLineColor(sample[2])

      cloned_histo = histos[i].Clone()
      cloned_histo.SetFillColor(sample[2])
      stackedHisto.Add(cloned_histo)

      # print(var + ":" + (str)(histos[i].Integral(0, histos[i].GetNbinsX() + 1)))
      if var == cut + "tau_pt_sum":
        error = ctypes.c_double()
        cutYields[sample[0]] = histos[i].IntegralAndError(0, histos[i].GetNbinsX() + 1, error)
        cutErrors[sample[0]] = error.value

      histos[i].Scale(1./histos[i].Integral())
      legName = sample[0] if sample[0] != "Jets" else "Z+jets"

      if histos[i].GetMaximum() > maximum:
        maximum = histos[i].GetMaximum()

      legnames.append(legName)

    for i in range(len(histos)):
      if i == 0:
        histos[i].SetMaximum(maximum * 1.1)
        histos[i].Draw('hist')
        histos[i].GetXaxis().SetTitle(varXAxis[variable])
      else:
        histos[i].Draw('histSAME')

      leg.AddEntry(histos[i],legnames[i], 'l')

    leg.Draw('SAME')

    #myText(0.19,0.76,kBlack,'#sqrt{s} = 13 TeV, 140 fb^{-1}')

    canv.SaveAs('plots/' + var + '.png')
    canv.Clear()

    stackedHisto.Draw('hist')
    stackedHisto.GetYaxis().SetTitleOffset(1.)
    stackedHisto.GetXaxis().SetTitleOffset(0.95)
    leg.Draw('SAME')
    stackedHisto.GetXaxis().SetTitle(varXAxis[variable])
    stackedHisto.GetYaxis().SetTitle(histos[i].GetYaxis().GetTitle())
    canv.SaveAs('stackPlots/stack_' + var + '.png')
    canv.Clear()

    # SB ratio plots
    var_sig1 = histos[3].Clone()
    var_sig2 = histos[3].Clone()
    total_background = histos[0].Clone()
    total_background.Add(histos[1])
    total_background.Add(histos[2])

    # Loop over the bins and calculate the S/sqrt(S+B) for each bin
    for i in range(1, histos[3].GetNbinsX() + 1):
      # Integrating up
      signalYield = histos[3].Integral(0, i)
      backgroundYield = total_background.Integral(0, i)
      try:
        SoverSqrtSB = signalYield/sqrt(signalYield + backgroundYield)
      except ZeroDivisionError:
        SoverSqrtSB = 0
      except ValueError:
        SoverSqrtSB = 0
      var_sig1.SetBinContent(i, SoverSqrtSB)

      # Integrating inverse
      signalYield = histos[3].Integral(i, histos[3].GetNbinsX() + 1)
      backgroundYield = total_background.Integral(i, histos[3].GetNbinsX() + 1)
      try:
        SoverSqrtSB = signalYield/sqrt(signalYield + backgroundYield)
      except ZeroDivisionError:
        SoverSqrtSB = 0
      except ValueError:
        SoverSqrtSB = 0
      var_sig2.SetBinContent(i, SoverSqrtSB)

    var_sig1.SetMaximum(var_sig1.GetMaximum() * 1.1)
    var_sig1.SetLineWidth(3)
    var_sig1.SetMarkerColor(kRed)
    var_sig1.SetLineColor(kRed)
    var_sig1.Draw('hist')
    var_sig1.GetXaxis().SetTitle(varXAxis[variable])
    var_sig1.GetXaxis().SetTitleOffset(1.)
    var_sig1.GetYaxis().SetTitle("S/#sqrt{S+B}")
    var_sig1.GetYaxis().SetTitleOffset(1.15)

    var_sig2.SetMarkerColor(kBlue)
    var_sig2.SetLineColor(kBlue)
    var_sig2.Draw('histSAME')
    var_sig2.GetXaxis().SetTitle(varXAxis[variable])
    canv.SaveAs('SBplots/SB_' + var + '.png')
    canv.Clear()

    ### SIGNIFICANCE PLOTTING ###
    if variable == "delta_Phi_ll":
      new_sig1 = histos[3].Clone()
      full_background = histos[0].Clone()
      full_background.Add(histos[1])
      full_background.Add(histos[2])

      for i in range(1, new_sig1.GetNbinsX() + 1):
        signal_yield = histos[3].GetBinContent(int(i))
        background_yield = full_background.GetBinContent(int(i))
        try:
          sb = signal_yield/sqrt(signal_yield + background_yield)
        except:
          sb = 0
        new_sig1.SetBinContent(i, sb)

      new_sig1.SetMaximum(new_sig1.GetBinContent(new_sig1.GetMaximumBin())*1.1)
      new_sig1.SetLineWidth(3)
      new_sig1.SetMarkerColor(kRed)
      new_sig1.SetLineColor(kRed)
      new_sig1.Draw('hist')
      new_sig1.GetYaxis().SetTitle("S/#sqrt{S+B}")
      new_sig1.GetYaxis().SetTitleOffset(1.1)
      new_sig1.GetXaxis().SetTitle(varXAxis[variable])
      new_sig1.GetXaxis().SetTitleOffset(0.95)

      canv.SaveAs("signedDeltaPhill/cutSoverSqrtSB" + cut + ".png")
      canv.Clear()
    ### END OF SB RATIO PLOTTING ###

  # Write the yields to a file
  f = open("plottingYields.txt", "a")
  backgroundYield = cutYields["llll"] + cutYields["other di-boson"] + cutYields["Jets"]
  backgroundError = sqrt(cutErrors["llll"]**2 + cutErrors["other di-boson"]**2 + cutErrors["Jets"]**2)

  s_over_b_error = sqrt(
    ((cutYields["signal"] + cutErrors["signal"])/backgroundYield
     - cutYields["signal"]/backgroundYield)**2
    + (cutYields["signal"]/(backgroundYield + backgroundError)
       - cutYields["signal"]/backgroundYield)**2
  )

  significance_error = sqrt(
    ((cutYields["signal"] + cutErrors["signal"])/sqrt(cutYields["signal"] + cutErrors["signal"] + backgroundYield)
     - cutYields["signal"]/sqrt(cutYields["signal"] + backgroundYield))**2
    + (cutYields["signal"]/sqrt(cutYields["signal"] + backgroundYield + backgroundError)
       - cutYields["signal"]/sqrt(cutYields["signal"] + backgroundYield))**2
  )

  f.write((str)(cut) + ": " + (str)(cutYields) + "\n errors: " + (str)(cutErrors) + "\n")
  f.write("S/B: " + (str)(cutYields["signal"]/backgroundYield) + " and error: " + (str)(s_over_b_error) + "\n")
  f.write("S/sqrt(S+B): " + (str)(cutYields["signal"]/sqrt(cutYields["signal"] + backgroundYield)) +
          " and error: " + (str)(significance_error) + "\n\n")
  f.close()
  # Print the yields
  print((str)(cut) + ": " + (str)(cutYields) + "\nerrors: " + (str)(cutErrors))
  print("S/B: " + (str)(cutYields["signal"]/backgroundYield) + " and error: " + (str)(s_over_b_error))
  print("S/sqrt(S+B): " + (str)(cutYields["signal"]/sqrt(cutYields["signal"] + backgroundYield)) +
        " and error: " + (str)(significance_error) + "\n")
