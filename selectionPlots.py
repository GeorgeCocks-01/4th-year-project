import ROOT
import copy, os, re, sys
import argparse
import math

Zmass = 91.1876

## Method to resolve regular expressions in file names.
#  TChain::Add only supports wildcards in the last items, i.e. on file level.
#  This method can resolve all wildcards at any directory level,
#  e.g. /my/directory/a*test*/pattern/*.root
#  @param pattern    the file name pattern using python regular expressions
#  @return list of all files matching the pattern
def findAllFilesInPath( pattern ,path ):
  files = []
  items = pattern.split( '/' )

  def checkPath( path, items ):
    # nested method to deal with the recursion
    import ROOT
    if not items:
      return
    myItems = copy.copy( items )
    item = myItems.pop(0)
    if '*' in item:
      directory = ROOT.gSystem.OpenDirectory( path )
      # beg and end of line control so that *truc does not match bla_truc_xyz
      item = "^"+item.replace( '*', '.*' )+"$"
      p = re.compile( item )
      entry = True
      while entry:
        entry = ROOT.gSystem.GetDirEntry( directory )
        if p.match( entry ):
          if not myItems:
            files.append( path + entry )
          else:
            checkPath( path + entry + '/', myItems)
      ROOT.gSystem.FreeDirectory( directory )
    elif item and not myItems:
      files.append( path + item )
    else:
      checkPath( path + item + '/', myItems )
  checkPath( path, items )
  return files

def fillHistograms(tau1, tauOrLep, Zlep1, Zlep2, met_p4, nJets, totalWeight, histograms):
  fillers = []

  fillers.append(tau1.Pt() + tauOrLep.Pt())
  fillers.append((Zlep1 + Zlep2).M())
  fillers.append(met_p4)
  fillers.append(Zlep1.DeltaR(Zlep2))
  fillers.append(tau1.DeltaR(tauOrLep))
  fillers.append(math.fabs(Zlep1.Eta() - Zlep2.Eta()))
  fillers.append(math.fabs(tau1.Eta() - tauOrLep.Eta()))
  fillers.append((tau1 + tauOrLep).DeltaR(Zlep1 + Zlep2))
  fillers.append(nJets)
  fillers.append(Zlep1.DeltaPhi(Zlep2))
  fillers.append(tau1.DeltaPhi(tauOrLep))
  fillers.append((Zlep1 + Zlep2).DeltaPhi(tau1 + tauOrLep))

  for i in range(0, len(histograms)): #fills histograms
    histograms[i].Fill(fillers[i], totalWeight)

def main(args):
  if (args.inputsample[-1] != "/"): #adds / to end of file path if not present
    args.inputsample += "/"
  directory = "rootData/" + args.inputsample
  pattern = "*.root"

  tree = ROOT.TChain("NOMINAL")
  nFiles = 0
  luminosity = 140000
  sumAllMC = 0
  for fileName in findAllFilesInPath(pattern, directory):
    nFiles += tree.Add(fileName)
    file = ROOT.TFile.Open(fileName)
    h = file.Get("h_metadata")
    sumAllMC += h.GetBinContent(8)
    file.Close()
  print(args.inputsample, ":", nFiles, "files")

  # define histograms
  diLepHistograms = [] #array for histograms of the two lepton cut
  diLepHistograms.append(ROOT.TH1D("2_lep_tau_pt_sum", "p_{T}^{#tau_sum};pT(GeV);Normalised Counts", 50, 0, 500))
  diLepHistograms.append(ROOT.TH1D("2_lep_lepton_mass_sum", "M(ll);Mass(GeV);Normalised Counts", 50, 0, 200))
  diLepHistograms.append(ROOT.TH1D("2_lep_met_pt", "met.Pt();pT(GeV);Normalised Counts", 50, 0, 500))
  diLepHistograms.append(ROOT.TH1D("2_lep_delta_R_Z", "delta_R_Z;Delta R(Rad);Normalised Counts", 50, 0, 5))
  diLepHistograms.append(ROOT.TH1D("2_lep_delta_R_H", "delta_R_H;Delta R(Rad);Normalised Counts", 50, 0, 5))
  diLepHistograms.append(ROOT.TH1D("2_lep_delta_Eta_Z", "delta_Eta_Z;Delta Eta(Rad);Normalised Counts", 50, 0, 5))
  diLepHistograms.append(ROOT.TH1D("2_lep_delta_Eta_H", "delta_Eta_H;Delta Eta(Rad);Normalised Counts", 50, 0, 5))
  diLepHistograms.append(ROOT.TH1D("2_lep_delta_R_tau_l", "delta_R_tl;Delta R(Rad);Normalised Counts", 50, 0, 5))
  diLepHistograms.append(ROOT.TH1D("2_lep_n_jets", "n_jets;n_jets;Normalised Counts", 10, 0, 10))
  diLepHistograms.append(ROOT.TH1D("2_lep_delta_phi_Z", "delta_phi_Z;Delta Phi(Rad);Normalised Counts", 50, -4, 4))
  diLepHistograms.append(ROOT.TH1D("2_lep_delta_phi_H", "delta_phi_H;Delta Phi(Rad);Normalised Counts", 50, -4, 4))
  diLepHistograms.append(ROOT.TH1D("2_lep_delta_phi_tau_l", "delta_eta_tl;Delta Phi(Rad);Normalised Counts", 50, -4, 4))

  triLepHistograms = [] #array for histograms of the three lepton cut
  histNames = ["3_lep_tau_pt_sum", "3_lep_Z_lepton_mass_sum", "3_lep_met_pt",
  "3_lep_delta_R_Z", "3_lep_delta_R_H", "3_lep_delta_Eta_Z", "3_lep_delta_Eta_H",
  "3_lep_delta_R_tau_l", "3_lep_n_jets", "3_lep_delta_phi_Z", "3_lep_delta_phi_H", "3_lep_delta_phi_tau_l"]

  for i in range(0, len(diLepHistograms)): #generates histograms for 3 lepton cut by cloning those from the 2 lep cut
    triLepHistograms.append(diLepHistograms[i].Clone(histNames[i]))
    diLepHistograms[i].Sumw2()
    triLepHistograms[i].Sumw2()

  diLepYield = 0
  triLepYield = 0

  zCandidate1 = 0.0
  zCandidate2 = 0.0

  #FILL HISTOGRAMS LOOP
  for i in range(0, tree.GetEntries()):
    tree.GetEntry(i)
    # vector of TLorentzVectors of the taus
    taus_p4 = getattr(tree, "taus_p4")
    leptons_p4 = getattr(tree, "leptons_p4")
    met_p4 = getattr(tree, "met_p4")
    nJets30 = getattr(tree, "n_jets_30")
    lFlavour = getattr(tree, "leptons")
    lCharge = getattr(tree, "leptons_q")
    tauCharge = getattr(tree, "taus_q")
    crossSection = getattr(tree, "cross_section")
    rnnID = getattr(tree, "taus_jet_rnn_medium")
    wTotal = (crossSection * luminosity * getattr(tree, "pu_NOMINAL_pileup_combined_weight") *
    getattr(tree, "weight_mc"))/sumAllMC #calculates weight for each event

    if len(taus_p4) > 0: #checks if there is a tau
      if len(leptons_p4) == 3: flavList = [lFlavour[0], lFlavour[1], lFlavour[2]] #list of lepton flavours
      # selection cut for 2 lepton final state
      if ((len(leptons_p4) == 2) and (len(taus_p4) == 2) and (lFlavour[0] == lFlavour[1]) and
      (lCharge[0] == -lCharge[1]) and (rnnID[0] == 1) and (rnnID[1] == 1) and (tauCharge[0] == -tauCharge[1])
      and (taus_p4[0].Pt() + taus_p4[1].Pt() > 75)):
        fillHistograms(taus_p4[0], taus_p4[1], leptons_p4[0], leptons_p4[1], met_p4.Pt(), nJets30, wTotal,
        diLepHistograms)
        diLepYield += wTotal


      # selection cut for 3 lepton final state
      elif ((len(leptons_p4) == 3) and len(taus_p4) == 1 and (rnnID[0] == 1) and (flavList.count(1) + flavList.count(2) == 3)):
        chargeList = [lCharge[0], lCharge[1], lCharge[2]] #list of lepton charges
        try:
          muIndex = flavList.index(1) #index of muon
          eIndex = flavList.index(2) #index of electron
        except ValueError:
          pass

        # One muon, two electrons
        if ((flavList.count(1) == 1) and (flavList.count(2) == 2) and (lCharge[muIndex] == -tauCharge[0])
        and (leptons_p4[muIndex].Pt() + taus_p4[0].Pt() > 60) and (lCharge[(muIndex + 1)%3] == -lCharge[(muIndex - 1)%3])
        ): #and (lFlavour[(muIndex + 1)%3] == lFlavour[(muIndex - 1)%3]) is implied

          fillHistograms(taus_p4[0], leptons_p4[muIndex], leptons_p4[(muIndex + 1)%3],
          leptons_p4[(muIndex - 1)%3], met_p4.Pt(), nJets30, wTotal, triLepHistograms)
          triLepYield += wTotal

        # Two muons, one electron
        elif ((flavList.count(2) == 1) and (flavList.count(1) == 2) and (lCharge[eIndex] == -tauCharge[0])
        and (leptons_p4[eIndex].Pt() + taus_p4[0].Pt() > 60) and (lCharge[(eIndex + 1)%3] == -lCharge[(eIndex - 1)%3])
        ): #and (lFlavour[(eIndex + 1)%3] == lFlavour[(eIndex - 1)%3]) is implied

          fillHistograms(taus_p4[0], leptons_p4[eIndex], leptons_p4[(eIndex + 1)%3],
          leptons_p4[(eIndex - 1)%3], met_p4.Pt(), nJets30, wTotal, triLepHistograms)
          triLepYield += wTotal

        # One positive charge, two negatives
        elif (chargeList.count(+1) == 1) and (chargeList.count(-1) == 2):
        #and (lCharge[(chargeList.index(+1) - 1)%3] == -lCharge[(chargeList.index(+1) + 1)%3])) is implied

          posIndex = chargeList.index(+1)
          zCandidate1 = math.fabs((leptons_p4[posIndex] + leptons_p4[(posIndex + 1)%3]).M() - Zmass)
          zCandidate2 = math.fabs((leptons_p4[posIndex] + leptons_p4[(posIndex - 1)%3]).M() - Zmass)

          if ((zCandidate1 < zCandidate2) and ((lCharge[(posIndex - 1)%3] == -tauCharge[0]))
          and (leptons_p4[(posIndex - 1)%3].Pt() + taus_p4[0].Pt() > 60)):

            fillHistograms(taus_p4[0], leptons_p4[(posIndex - 1)%3], leptons_p4[posIndex],
             leptons_p4[(posIndex + 1)%3], met_p4.Pt(), nJets30, wTotal, triLepHistograms)
            triLepYield += wTotal

          elif ((zCandidate1 > zCandidate2) and ((lCharge[(posIndex + 1)%3] == -tauCharge[0]))
          and (leptons_p4[(posIndex + 1)%3].Pt() + taus_p4[0].Pt() > 60)):

            fillHistograms(taus_p4[0], leptons_p4[(posIndex + 1)%3], leptons_p4[posIndex],
             leptons_p4[(posIndex - 1)%3], met_p4.Pt(), nJets30, wTotal, triLepHistograms)
            triLepYield += wTotal

        # Two positive charges, one negative
        elif (chargeList.count(-1) == 1) and (chargeList.count(+1) == 2):
        #and(lCharge[(chargeList.index(-1) - 1)%3] == -lCharge[(chargeList.index(-1) + 1)%3])): is implied

          negIndex = chargeList.index(-1)
          zCandidate1 = math.fabs((leptons_p4[negIndex] + leptons_p4[(negIndex + 1)%3]).M() - Zmass)
          zCandidate2 = math.fabs((leptons_p4[negIndex] + leptons_p4[(negIndex - 1)%3]).M() - Zmass)

          if ((zCandidate1 < zCandidate2) and ((lCharge[(negIndex - 1)%3] == -tauCharge[0]))
          and (leptons_p4[(negIndex - 1)%3].Pt() + taus_p4[0].Pt() > 60)):

            fillHistograms(taus_p4[0], leptons_p4[(negIndex - 1)%3], leptons_p4[negIndex],
             leptons_p4[(negIndex + 1)%3], met_p4.Pt(), nJets30, wTotal, triLepHistograms)
            triLepYield += wTotal

          elif ((zCandidate1 > zCandidate2) and ((lCharge[(negIndex + 1)%3] == -tauCharge[0]))
          and (leptons_p4[(negIndex + 1)%3].Pt() + taus_p4[0].Pt() > 60)):

            fillHistograms(taus_p4[0], leptons_p4[(negIndex + 1)%3], leptons_p4[negIndex],
             leptons_p4[(negIndex - 1)%3], met_p4.Pt(), nJets30, wTotal, triLepHistograms)
            triLepYield += wTotal


  print("2lep selection cut:", diLepYield)
  print("3lep selection cut:", triLepYield)

  if (args.outputfile[-5:] != ".root"): #adds .root to end of output file if not present
    args.outputfile += ".root"
  args.outputfile = "outputRoot/" + args.outputfile
  outHistFile = ROOT.TFile.Open(args.outputfile, "RECREATE")
  outHistFile.cd()

  for i in range(0, len(diLepHistograms)): #writes all histograms
    diLepHistograms[i].Write()
    triLepHistograms[i].Write()

  outHistFile.Close()

  del tree

if __name__ == "__main__":
  # parse the CLI arguments
  parser = argparse.ArgumentParser(description='script to run over ntuple dataset')
  parser.add_argument('--inputsample', '-i', metavar='INPUT', type=str, dest="inputsample", default="ZHlltt/", help='directory for input root files')
  parser.add_argument('--outputfile', '-o', metavar='OUTPUT', type=str, dest="outputfile", default="lltautauhistograms.root", help='outputfile for process')
  args = parser.parse_args()

  # call the main function
  main(args)
