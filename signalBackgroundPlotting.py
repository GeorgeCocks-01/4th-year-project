from ROOT import *
import copy, os, re, sys
import argparse
from selectionPlots import findAllFilesInPath

gROOT.LoadMacro('../atlasrootstyle/AtlasStyle.C')
gROOT.LoadMacro('../atlasrootstyle/AtlasUtils.C')
gROOT.SetBatch(kTRUE)
SetAtlasStyle()

canv = TCanvas('c','c',600,600)
canv.cd()
colorList = [kBlack,kRed,kBlue,kGreen,kViolet,kMagenta,kAzure,kOrange,kYellow,kMagenta+3,kCyan,kYellow+2]

zJetsSamples = []
zJetsSamples.extend(findAllFilesInPath("*Zee*.root", "outputRoot/"))
zJetsSamples.extend(findAllFilesInPath("*Zmumu*.root", "outputRoot/"))
zJetsSamples.extend(findAllFilesInPath("*Ztt*.root", "outputRoot/"))

samples = (('llll', ('outputRoot/llll-weighted.root',), kBlack),
      ('other di-boson', ('outputRoot/ZqqZll-weighted.root',
        'outputRoot/lllv-weighted.root',
        'outputRoot/llvv-weighted.root',
        'outputRoot/WqqZll-weighted.root',
        'outputRoot/ttH-weighted.root'), kBlue),
      ('Jets', zJetsSamples, kGreen),
      ('signal', ('outputRoot/ZH-weighted.root', 'outputRoot/ggZH-weighted.root'), kRed))

varList = ["tau_pt_sum", "Z_lepton_mass_sum", "met_pt", "delta_R_ll", "delta_R_tt",
"delta_Eta_ll", "delta_Eta_tt", "delta_R_tt_ll", "n_jets", "delta_phi_ll",
"delta_phi_tt", "delta_phi_ll_tt", "mmc_mass"]

for cutNum in range(2,4): # Loop over the different selection cuts
  cut = str(cutNum) + "_lep_"
  for var in varList: # Loop over the variables
    var = cut + var
    leg = TLegend(0.7,0.6,0.8,0.85)
    leg.SetBorderSize(0)
    leg.SetTextSize(0.03)
    leg.SetEntrySeparation(0.001)

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

      stackedHisto.Add(histos[i].Clone())

      histos[i].Scale(1./histos[i].Integral())
      legName = sample[0]

      if histos[i].GetMaximum() > maximum:
        maximum = histos[i].GetMaximum()

      legnames.append(legName)

    for i in range(len(histos)):
      if i == 0:
        histos[i].SetMaximum(maximum * 1.3)
        histos[i].Draw('hist')
      else:
        histos[i].Draw('histSAME')

      leg.AddEntry(histos[i],legnames[i], 'l')


    leg.Draw('SAME')

    #myText(0.19,0.76,kBlack,'#sqrt{s} = 13 TeV, 140 fb^{-1}')

    canv.SaveAs('plots/' + var + '.pdf')
    canv.Clear()
    # stackedHisto.SetLineWidth(3)
    # stackedHisto.SetMarkerColor(sample[2])
    # stackedHisto.SetLineColor(sample[2])

    # stackedHisto.SetMaximum(maximum * 1.3)
    stackedHisto.Draw('hist')
    leg.Draw('SAME')
    stackedHisto.GetXaxis().SetTitle(histos[i].GetXaxis().GetTitle())
    stackedHisto.GetYaxis().SetTitle(histos[i].GetYaxis().GetTitle())
    canv.SaveAs('stackPlots/stack_' + var + '.pdf')
