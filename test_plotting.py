from ROOT import *
import copy, os, re, sys
import argparse

gROOT.LoadMacro('/storage/epp2/phsngj/Htautau/CAF/hlepcaf/tools/atlasrootstyle/AtlasStyle.C')
gROOT.LoadMacro('/storage/epp2/phsngj/Htautau/CAF/hlepcaf/tools/atlasrootstyle/AtlasUtils.C')
gROOT.SetBatch(kTRUE)
SetAtlasStyle()

canv = TCanvas('c','c',600,600)
canv.cd()
colorList = [kBlack,kRed,kBlue,kGreen,kViolet,kMagenta,kAzure,kViolet,kOrange,kYellow,kMagenta+3,kCyan,kYellow+2]

samples = [('ZH','Ztt/ZH2elptons.root', kRed),
       ('ZZ', 'Ztt/ZZ2leptons.root', kBlue)
        ]


varList = ['lep0_pt','lep1_pt']

for var in varList:

  leg = TLegend(0.7,0.7,0.8,0.85)
  leg.SetBorderSize(0)
  leg.SetTextSize(0.03)
  leg.SetEntrySeparation(0.001)

  counter = 0
  histos=[]
  legnames=[]
  maximum = -999.
  for sample in samples:
    infile = TFile.Open(sample[1],"READ")
    histo = infile.Get(var)
    histo.SetDirectory(0)
    infile.Close()
    legName = sample[0]

    histo.Scale(1/histo.Integral())

    if histo.GetMaximum() > maximum:
      maximum = histo.GetMaximum()

    histo.SetLineWidth(3)
    histo.SetMarkerColor(sample[2])
    histo.SetLineColor(sample[2])
    histos.append(histo)
    legnames.append(legName)

  for i in range(0,len(histos)):

    if i == 0:
      histos[i].SetMaximum(maximum * 1.3)
      histos[i].Draw('hist')
    else:
      histos[i].Draw('histSAME')

    leg.AddEntry(histos[i],legnames[i],'l')


  leg.Draw('SAME')

  #myText(0.19,0.76,kBlack,'#sqrt{s} = 13 TeV, 140 fb^{-1}')

  canv.SaveAs('ShapePlot_'+var+'.pdf')
  canv.Clear()

