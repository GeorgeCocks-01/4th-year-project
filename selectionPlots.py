import ROOT
import copy, os, re, sys
import argparse
import math
from array import array

REALZMASS = 91.1876

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

def fillHistograms(tau1, tauOrLep, Zlep1, Zlep2, met_p4, nJets, mmc, totalWeight, nTuples, newTree, histograms = None):
  fillers = dict.fromkeys(nTuples.keys())
  del fillers["weight"]

  fillers["tauPtSum"] = tau1.Pt() + tauOrLep.Pt()
  fillers["zMassSum"] = (Zlep1 + Zlep2).M()
  fillers["metPt"] = (met_p4)
  fillers["deltaRll"] = (Zlep1.DeltaR(Zlep2))
  fillers["deltaRtt"] = (tau1.DeltaR(tauOrLep))
  fillers["deltaEtall"] = (math.fabs(Zlep1.Eta() - Zlep2.Eta()))
  fillers["deltaEtatt"] = (math.fabs(tau1.Eta() - tauOrLep.Eta()))
  fillers["deltaRttll"] = ((tau1 + tauOrLep).DeltaR(Zlep1 + Zlep2))
  fillers["nJets"] = (nJets)
  if (Zlep1.Eta() > Zlep2.Eta()):
    fillers["deltaPhill"] = (Zlep1.DeltaPhi(Zlep2))
  else:
    fillers["deltaPhill"] = (Zlep2.DeltaPhi(Zlep1))
  fillers["deltaPhitt"] = (tau1.DeltaPhi(tauOrLep))
  fillers["deltaPhilltt"] = ((Zlep1 + Zlep2).DeltaPhi(tau1 + tauOrLep))
  fillers["mmc"] = (mmc)

  if histograms is not None:
    for key in fillers:
      nTuples[key][0] = fillers[key] # fills nTuples with values
      histograms[key].Fill(fillers[key], totalWeight) #fills histograms
  else:
    for key in fillers:
      nTuples[key][0] = fillers[key]

  nTuples["weight"][0] = totalWeight
  newTree.Fill()

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
    if args.inputsample[:-1] == "ZHlltt":
      h = file.Get("h_metadata_theory_weights")
      sumAllMC += h.GetBinContent(110)
    elif args.inputsample[:-1] == "ggZH":
      h = file.Get("h_metadata_theory_weights")
      sumAllMC += h.GetBinContent(111)
    else:
      h = file.Get("h_metadata")
      sumAllMC += h.GetBinContent(8)
    file.Close()
  print(args.inputsample, ":", nFiles, "files")

  # define histogram dictionaries
  diLepHistograms = {
    "tauPtSum": ROOT.TH1D("2_lep_tau_pt_sum", "p_{T}^{#tau_sum};pT(GeV);Normalised Counts", 50, 50, 350),
    "zMassSum": ROOT.TH1D("2_lep_Z_lepton_mass_sum", "M(ll);Mass(GeV);Normalised Counts", 50, 70, 115),
    "metPt": ROOT.TH1D("2_lep_met_pt", "met.Pt();pT(GeV);Normalised Counts", 50, 0, 350),
    "deltaRll": ROOT.TH1D("2_lep_delta_R_ll", "delta_R_ll;Delta R(Rad);Normalised Counts", 50, 0, 5),
    "deltaRtt": ROOT.TH1D("2_lep_delta_R_tt", "delta_R_tt;Delta R(Rad);Normalised Counts", 50, 0, 5),
    "deltaEtall":ROOT.TH1D("2_lep_delta_Eta_ll", "delta_Eta_ll;Delta Eta(Rad);Normalised Counts", 50, 0, 5),
    "deltaEtatt":ROOT.TH1D("2_lep_delta_Eta_tt", "delta_Eta_tt;Delta Eta(Rad);Normalised Counts", 50, 0, 5),
    "deltaRttll": ROOT.TH1D("2_lep_delta_R_tt_ll", "delta_R_ttll;Delta R(Rad);Normalised Counts", 50, 0, 5),
    "nJets": ROOT.TH1D("2_lep_n_jets", "n_jets;n_jets;Normalised Counts", 10, 0, 10),
    "deltaPhill": ROOT.TH1D("2_lep_delta_Phi_ll", "delta_Phi_ll;Delta Phi(Rad);Normalised Counts", 50, -4, 4),
    "deltaPhitt": ROOT.TH1D("2_lep_delta_Phi_tt", "delta_Phi_tt;Delta Phi(Rad);Normalised Counts", 50, -4, 4),
    "deltaPhilltt": ROOT.TH1D("2_lep_delta_Phi_ll_tt", "delta_Phi_lltt;Delta Phi(Rad);Normalised Counts", 50, -4, 4),
    "mmc": ROOT.TH1D("2_lep_mmc_mass", "MMC_mass;Mass(GeV);Normalised Counts", 50, 0, 300)
  }
  triLepHistograms = dict.fromkeys(diLepHistograms.keys()) # list for histograms of the three lepton cut

  # loop through dictionary diLepHistograms and copy histograms to triLepHistograms
  for key in diLepHistograms:
    triLepHistograms[key] = diLepHistograms[key].Clone("3" + diLepHistograms[key].GetName()[1:])
    diLepHistograms[key].Sumw2()
    triLepHistograms[key].Sumw2()


  ### NTUPLE INITIALISATION ###
  # if outputntfile is not specified, generate from input sample
  if (args.outputntfile == None):
    outputNtName = args.inputsample[:-1] + ".root"
  else: # if outputntfile is specified, use that
    if (args.outputntfile[-5:] != ".root"): #adds .root to end of output file if not present
      args.outputntfile += ".root"
    outputNtName = args.outputntfile

  # Create ntuple output file
  outNtupleFile = ROOT.TFile.Open(("outputNTuples/" + outputNtName), "RECREATE")
  newTree2Lep = ROOT.TTree("nominal2lep", "nominal2lep")
  newTree3Lep = ROOT.TTree("nominal3lep", "nominal3lep")

  nTuples2Lep = dict.fromkeys(diLepHistograms.keys()) # list for nTuples from diLepHistograms
  nTuples3Lep = dict.fromkeys(diLepHistograms.keys()) # list for nTuples from triLepHistograms

  for i in nTuples2Lep:
    nTuples2Lep[i] = array('f', [0])
    nTuples3Lep[i] = array('f', [0])
    newTree2Lep.Branch(i, nTuples2Lep[i], i + "/F")
    newTree3Lep.Branch(i, nTuples3Lep[i], i + "/F")
  nTuples2Lep["weight"] = array('f', [0]) # Add weight branch
  newTree2Lep.Branch("weight", nTuples2Lep["weight"], "weight/F")
  nTuples3Lep["weight"] = array('f', [0]) # Add weight branch
  newTree3Lep.Branch("weight", nTuples3Lep["weight"], "weight/F")

  #FILL HISTOGRAMS LOOP
  for i in range(0, tree.GetEntries()):
    tree.GetEntry(i)

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
    leptonsIDTight = getattr(tree, "leptons_id_tight")
    tauBdt = getattr(tree, "taus_ele_bdt_loose_retuned")
    eIsoPass = getattr(tree, "leptons_iso_FCLoose")
    muIsoPass = getattr(tree, "leptons_iso_TightTrackOnly_FixedRad")

    if len(taus_p4) > 0: #checks if there is a tau
      if len(leptons_p4) == 3: flavList = [lFlavour[0], lFlavour[1], lFlavour[2]] #list of lepton flavours

      #### SELECTION CUT for 2 lepton final state ####
      if ((len(leptons_p4) == 2) and (len(taus_p4) == 2) and (lFlavour[0] == lFlavour[1])
        and (lCharge[0] == -lCharge[1]) and (rnnID[0] == 1) and (rnnID[1] == 1) and (tauCharge[0] == -tauCharge[1])
        and (taus_p4[0].Pt() + taus_p4[1].Pt() > 75) and ((leptons_p4[0] + leptons_p4[1]).M() > 71)
        and ((leptons_p4[0] + leptons_p4[1]).M() < 111) and (leptonsIDTight[0] == 1) and (leptonsIDTight[1] == 1)
        and ((lFlavour[0] == 1 and muIsoPass[0] == 1 and muIsoPass[1] == 1)
        or (lFlavour[0] == 2 and eIsoPass[0] == 1 and eIsoPass[1] == 1)) and (tauBdt[0] == 1) and (tauBdt[1] == 1)):
        tau0tau1MMC = getattr(tree, "mmc_tau0_tau1_mmc_mlm_m")
        # if fill nTuples or not
        if ((taus_p4[0].DeltaR(taus_p4[1]) < 3.1) and (leptons_p4[0].DeltaR(leptons_p4[1]) < 3)
          and ((taus_p4[0] + taus_p4[1]).DeltaR(leptons_p4[0] + leptons_p4[1]) < 3.9)
          and (math.fabs(taus_p4[0].Eta() - taus_p4[1].Eta()) < 1.9)
          and (math.fabs(leptons_p4[0].Eta() - leptons_p4[1].Eta()) < 3.5)): # different value for 2 lepton cut
          # define deltaPhill for selection cut
          if (leptons_p4[0].Eta() > leptons_p4[1].Eta()):
            deltaPhill = (leptons_p4[0].DeltaPhi(leptons_p4[1]))
          else:
            deltaPhill = (leptons_p4[1].DeltaPhi(leptons_p4[0]))

          if (deltaPhill > -3.2 and deltaPhill < 2.4 and tau0tau1MMC > 90 and tau0tau1MMC < 190):
            fillHistograms(taus_p4[0], taus_p4[1], leptons_p4[0], leptons_p4[1], met_p4.Pt(), nJets30, tau0tau1MMC,
            wTotal, nTuples2Lep, newTree2Lep, diLepHistograms)
        else:
          fillHistograms(taus_p4[0], taus_p4[1], leptons_p4[0], leptons_p4[1], met_p4.Pt(), nJets30, tau0tau1MMC,
          wTotal, nTuples2Lep, newTree2Lep)

      #### SELECTION CUT for 3 lepton final state ####
      elif ((len(leptons_p4) == 3) and len(taus_p4) == 1 and (rnnID[0] == 1)
        and (flavList.count(1) + flavList.count(2) == 3) and (leptonsIDTight[0] == 1) and (leptonsIDTight[1] == 1)
        and (leptonsIDTight[2] == 1) and (tauBdt[0] == 1)):
        chargeList = [lCharge[0], lCharge[1], lCharge[2]] #list of lepton charges
        try:
          muIndex = flavList.index(1) #index of muon
          eIndex = flavList.index(2) #index of electron
        except ValueError:
          pass

        # One muon, two electrons
        if ((flavList.count(1) == 1) and (flavList.count(2) == 2) and (lCharge[muIndex] == -tauCharge[0])
          and (leptons_p4[muIndex].Pt() + taus_p4[0].Pt() > 60)
          and (lCharge[(muIndex + 1)%3] == -lCharge[(muIndex - 1)%3])
          and ((leptons_p4[(muIndex + 1)%3] + leptons_p4[(muIndex - 1)%3]).M() > 81)
          and ((leptons_p4[(muIndex + 1)%3] + leptons_p4[(muIndex - 1)%3]).M() < 101) and (muIsoPass[muIndex] == 1)
          and (eIsoPass[(muIndex + 1)%3] == 1) and (eIsoPass[(muIndex - 1)%3] == 1)):
          tau0lepMMC = getattr(tree, "mmc_tau0_lep" + str(muIndex) + "_mmc_mlm_m")
          # if fill nTuples or not
          if ((taus_p4[0].DeltaR(leptons_p4[muIndex]) < 3.1)
            and (leptons_p4[(muIndex + 1)%3].DeltaR(leptons_p4[(muIndex - 1)%3]) < 3)
            and ((taus_p4[0] + leptons_p4[muIndex]).DeltaR(leptons_p4[(muIndex + 1)%3]
            + leptons_p4[(muIndex - 1)%3]) < 3.9)
            and (math.fabs(taus_p4[0].Eta() - leptons_p4[muIndex].Eta()) < 1.9)
            and (math.fabs(leptons_p4[(muIndex + 1)%3].Eta() - leptons_p4[(muIndex - 1)%3].Eta()) < 2.7)):
            #and (lFlavour[(muIndex + 1)%3] == lFlavour[(muIndex - 1)%3]) is implied

            if (leptons_p4[(muIndex + 1)%3].Eta() > leptons_p4[(muIndex - 1)%3].Eta()):
              deltaPhill = (leptons_p4[(muIndex + 1)%3].DeltaPhi(leptons_p4[(muIndex - 1)%3]))
            else:
              deltaPhill = (leptons_p4[(muIndex - 1)%3].DeltaPhi(leptons_p4[(muIndex + 1)%3]))

            if (deltaPhill > -3.2 and deltaPhill < 2.4 and tau0lepMMC > 90 and tau0lepMMC < 190):
              fillHistograms(taus_p4[0], leptons_p4[muIndex], leptons_p4[(muIndex + 1)%3],
                            leptons_p4[(muIndex - 1)%3], met_p4.Pt(), nJets30, tau0lepMMC, wTotal,
                            nTuples3Lep, newTree3Lep, triLepHistograms)
          else:
            fillHistograms(taus_p4[0], leptons_p4[muIndex], leptons_p4[(muIndex + 1)%3],
                          leptons_p4[(muIndex - 1)%3], met_p4.Pt(), nJets30, tau0lepMMC, wTotal,
                          nTuples3Lep, newTree3Lep)

        # Two muons, one electron
        elif ((flavList.count(2) == 1) and (flavList.count(1) == 2) and (lCharge[eIndex] == -tauCharge[0])
          and (leptons_p4[eIndex].Pt() + taus_p4[0].Pt() > 60)
          and (lCharge[(eIndex + 1)%3] == -lCharge[(eIndex - 1)%3])
          and ((leptons_p4[(eIndex + 1)%3] + leptons_p4[(eIndex - 1)%3]).M() > 81)
          and ((leptons_p4[(eIndex + 1)%3] + leptons_p4[(eIndex - 1)%3]).M() < 101) and (eIsoPass[eIndex] == 1)
          and (muIsoPass[(eIndex + 1)%3] == 1) and (muIsoPass[(eIndex - 1)%3] == 1)):
          tau0lepMMC = getattr(tree, "mmc_tau0_lep" + str(eIndex) + "_mmc_mlm_m")
          # if fill nTuples or not
          if ((taus_p4[0].DeltaR(leptons_p4[eIndex]) < 3.1)
            and (leptons_p4[(eIndex + 1)%3].DeltaR(leptons_p4[(eIndex - 1)%3]) < 3)
            and ((taus_p4[0] + leptons_p4[eIndex]).DeltaR(leptons_p4[(eIndex + 1)%3]
            + leptons_p4[(eIndex - 1)%3]) < 3.9)
            and (math.fabs(taus_p4[0].Eta() - leptons_p4[eIndex].Eta()) < 1.9)
            and (math.fabs(leptons_p4[(eIndex + 1)%3].Eta() - leptons_p4[(eIndex - 1)%3].Eta()) < 2.7)):
            #and (lFlavour[(eIndex + 1)%3] == lFlavour[(eIndex - 1)%3]) is implied

            if (leptons_p4[(eIndex + 1)%3].Eta() > leptons_p4[(eIndex - 1)%3].Eta()):
              deltaPhill = (leptons_p4[(eIndex + 1)%3].DeltaPhi(leptons_p4[(eIndex - 1)%3]))
            else:
              deltaPhill = (leptons_p4[(eIndex - 1)%3].DeltaPhi(leptons_p4[(eIndex + 1)%3]))

            if (deltaPhill > -3.2 and deltaPhill < 2.4 and tau0lepMMC > 90 and tau0lepMMC < 190):
              fillHistograms(taus_p4[0], leptons_p4[eIndex], leptons_p4[(eIndex + 1)%3],
                            leptons_p4[(eIndex - 1)%3], met_p4.Pt(), nJets30, tau0lepMMC, wTotal,
                            nTuples3Lep, newTree3Lep, triLepHistograms)
          else:
            fillHistograms(taus_p4[0], leptons_p4[eIndex], leptons_p4[(eIndex + 1)%3],
                            leptons_p4[(eIndex - 1)%3], met_p4.Pt(), nJets30, tau0lepMMC, wTotal,
                            nTuples3Lep, newTree3Lep)

        # One positive charge, two negatives
        elif ((chargeList.count(+1) == 1) and (chargeList.count(-1) == 2)
          and ((flavList.count(1) == 3 and muIsoPass[0] == 1 and muIsoPass[1] == 1 and muIsoPass[2] == 1)
          or (flavList.count(2) == 3 and eIsoPass[0] == 1 and eIsoPass[1] == 1 and eIsoPass[2] == 1))):
          #and (lCharge[(chargeList.index(+1) - 1)%3] == -lCharge[(chargeList.index(+1) + 1)%3])) is implied

          posIndex = chargeList.index(+1)
          zMass1 = (leptons_p4[posIndex] + leptons_p4[(posIndex + 1)%3]).M()
          zMass2 = (leptons_p4[posIndex] + leptons_p4[(posIndex - 1)%3]).M()
          zCandidate1 = math.fabs(zMass1 - REALZMASS)
          zCandidate2 = math.fabs(zMass2 - REALZMASS)

          if ((zCandidate1 < zCandidate2) and ((lCharge[(posIndex - 1)%3] == -tauCharge[0]))
            and (leptons_p4[(posIndex - 1)%3].Pt() + taus_p4[0].Pt() > 60) and (zMass1 > 81) and (zMass1 < 101)):
            tau0lepMMC = getattr(tree, "mmc_tau0_lep" + str((posIndex - 1)%3) + "_mmc_mlm_m")
            # if fill nTuples or not
            if ((taus_p4[0].DeltaR(leptons_p4[(posIndex - 1)%3]) < 3.1)
              and (leptons_p4[posIndex].DeltaR(leptons_p4[(posIndex + 1)%3]) < 3)
              and ((taus_p4[0] + leptons_p4[(posIndex - 1)%3]).DeltaR(leptons_p4[posIndex]
              + leptons_p4[(posIndex + 1)%3]) < 3.9)
              and (math.fabs(taus_p4[0].Eta() - leptons_p4[(posIndex - 1)%3].Eta()) < 1.9)
              and (math.fabs(leptons_p4[posIndex].Eta() - leptons_p4[(posIndex + 1)%3].Eta()) < 2.7)):

              if (leptons_p4[posIndex].Eta() > leptons_p4[(posIndex + 1)%3].Eta()):
                deltaPhill = (leptons_p4[posIndex].DeltaPhi(leptons_p4[(posIndex + 1)%3]))
              else:
                deltaPhill = (leptons_p4[(posIndex + 1)%3].DeltaPhi(leptons_p4[posIndex]))

              if (deltaPhill > -3.2 and deltaPhill < 2.4 and tau0lepMMC > 90 and tau0lepMMC < 190):
                fillHistograms(taus_p4[0], leptons_p4[(posIndex - 1)%3], leptons_p4[posIndex],
                              leptons_p4[(posIndex + 1)%3], met_p4.Pt(), nJets30, tau0lepMMC, wTotal,
                              nTuples3Lep, newTree3Lep, triLepHistograms)
            else:
              fillHistograms(taus_p4[0], leptons_p4[(posIndex - 1)%3], leptons_p4[posIndex],
                              leptons_p4[(posIndex + 1)%3], met_p4.Pt(), nJets30, tau0lepMMC, wTotal,
                              nTuples3Lep, newTree3Lep)

          elif ((zCandidate1 > zCandidate2) and ((lCharge[(posIndex + 1)%3] == -tauCharge[0]))
            and (leptons_p4[(posIndex + 1)%3].Pt() + taus_p4[0].Pt() > 60) and (zMass2 > 81) and (zMass2 < 101)):
            tau0lepMMC = getattr(tree, "mmc_tau0_lep" + str((posIndex + 1)%3) + "_mmc_mlm_m")
            # if fill nTuples or not
            if ((taus_p4[0].DeltaR(leptons_p4[(posIndex + 1)%3]) < 3.1)
              and (leptons_p4[posIndex].DeltaR(leptons_p4[(posIndex - 1)%3]) < 3)
              and ((taus_p4[0] + leptons_p4[(posIndex + 1)%3]).DeltaR(leptons_p4[posIndex]
              + leptons_p4[(posIndex - 1)%3]) < 3.9)
              and (math.fabs(taus_p4[0].Eta() - leptons_p4[(posIndex + 1)%3].Eta()) < 1.9)
              and (math.fabs(leptons_p4[posIndex].Eta() - leptons_p4[(posIndex - 1)%3].Eta()) < 2.7)):

              if (leptons_p4[posIndex].Eta() > leptons_p4[(posIndex - 1)%3].Eta()):
                deltaPhill = (leptons_p4[posIndex].DeltaPhi(leptons_p4[(posIndex - 1)%3]))
              else:
                deltaPhill = (leptons_p4[(posIndex - 1)%3].DeltaPhi(leptons_p4[posIndex]))

              if (deltaPhill > -3.2 and deltaPhill < 2.4 and tau0lepMMC > 90 and tau0lepMMC < 190):
                fillHistograms(taus_p4[0], leptons_p4[(posIndex + 1)%3], leptons_p4[posIndex],
                              leptons_p4[(posIndex - 1)%3], met_p4.Pt(), nJets30, tau0lepMMC, wTotal,
                              nTuples3Lep, newTree3Lep, triLepHistograms)
            else:
              fillHistograms(taus_p4[0], leptons_p4[(posIndex + 1)%3], leptons_p4[posIndex],
                              leptons_p4[(posIndex - 1)%3], met_p4.Pt(), nJets30, tau0lepMMC, wTotal,
                              nTuples3Lep, newTree3Lep)

        # Two positive charges, one negative
        elif ((chargeList.count(-1) == 1) and (chargeList.count(+1) == 2)
          and ((flavList.count(1) == 3 and muIsoPass[0] == 1 and muIsoPass[1] == 1 and muIsoPass[2] == 1)
          or (flavList.count(2) == 3 and eIsoPass[0] == 1 and eIsoPass[1] == 1 and eIsoPass[2] == 1))):
          #and(lCharge[(chargeList.index(-1) - 1)%3] == -lCharge[(chargeList.index(-1) + 1)%3])): is implied

          negIndex = chargeList.index(-1)
          zMass1 = (leptons_p4[negIndex] + leptons_p4[(negIndex + 1)%3]).M()
          zMass2 = (leptons_p4[negIndex] + leptons_p4[(negIndex - 1)%3]).M()
          zCandidate1 = math.fabs(zMass1 - REALZMASS)
          zCandidate2 = math.fabs(zMass2 - REALZMASS)

          if ((zCandidate1 < zCandidate2) and ((lCharge[(negIndex - 1)%3] == -tauCharge[0]))
            and (leptons_p4[(negIndex - 1)%3].Pt() + taus_p4[0].Pt() > 60) and (zMass1 > 81) and (zMass1 < 101)):
            tau0lepMMC = getattr(tree, "mmc_tau0_lep" + str((negIndex - 1)%3) + "_mmc_mlm_m")
            # if fill nTuples or not
            if ((taus_p4[0].DeltaR(leptons_p4[(negIndex - 1)%3]) < 3.1)
              and (leptons_p4[negIndex].DeltaR(leptons_p4[(negIndex + 1)%3]) < 3)
              and ((taus_p4[0] + leptons_p4[(negIndex - 1)%3]).DeltaR(leptons_p4[negIndex]
              + leptons_p4[(negIndex + 1)%3]) < 3.9)
              and (math.fabs(taus_p4[0].Eta() - leptons_p4[(negIndex - 1)%3].Eta()) < 1.9)
              and (math.fabs(leptons_p4[negIndex].Eta() - leptons_p4[(negIndex + 1)%3].Eta()) < 2.7)):

              if (leptons_p4[negIndex].Eta() > leptons_p4[(negIndex + 1)%3].Eta()):
                deltaPhill = (leptons_p4[negIndex].DeltaPhi(leptons_p4[(negIndex + 1)%3]))
              else:
                deltaPhill = (leptons_p4[(negIndex + 1)%3].DeltaPhi(leptons_p4[negIndex]))

              if (deltaPhill > -3.2 and deltaPhill < 2.4 and tau0lepMMC > 90 and tau0lepMMC < 190):
                fillHistograms(taus_p4[0], leptons_p4[(negIndex - 1)%3], leptons_p4[negIndex],
                              leptons_p4[(negIndex + 1)%3], met_p4.Pt(), nJets30, tau0lepMMC, wTotal,
                              nTuples3Lep, newTree3Lep, triLepHistograms)
            else:
              fillHistograms(taus_p4[0], leptons_p4[(negIndex - 1)%3], leptons_p4[negIndex],
                              leptons_p4[(negIndex + 1)%3], met_p4.Pt(), nJets30, tau0lepMMC, wTotal,
                              nTuples3Lep, newTree3Lep)

          elif ((zCandidate1 > zCandidate2) and ((lCharge[(negIndex + 1)%3] == -tauCharge[0]))
            and (leptons_p4[(negIndex + 1)%3].Pt() + taus_p4[0].Pt() > 60) and (zMass2 > 81) and (zMass2 < 101)):
            tau0lepMMC = getattr(tree, "mmc_tau0_lep" + str((negIndex + 1)%3) + "_mmc_mlm_m")
            # if fill nTuples or not
            if ((taus_p4[0].DeltaR(leptons_p4[(negIndex + 1)%3]) < 3.1)
              and (leptons_p4[negIndex].DeltaR(leptons_p4[(negIndex - 1)%3]) < 3)
              and ((taus_p4[0] + leptons_p4[(negIndex + 1)%3]).DeltaR(leptons_p4[negIndex]
              + leptons_p4[(negIndex - 1)%3]) < 3.9)
              and (math.fabs(taus_p4[0].Eta() - leptons_p4[(negIndex + 1)%3].Eta()) < 1.9)
              and (math.fabs(leptons_p4[negIndex].Eta() - leptons_p4[(negIndex - 1)%3].Eta()) < 2.7)):

              if (leptons_p4[negIndex].Eta() > leptons_p4[(negIndex - 1)%3].Eta()):
                deltaPhill = (leptons_p4[negIndex].DeltaPhi(leptons_p4[(negIndex - 1)%3]))
              else:
                deltaPhill = (leptons_p4[(negIndex - 1)%3].DeltaPhi(leptons_p4[negIndex]))

              if (deltaPhill > -3.2 and deltaPhill < 2.4 and tau0lepMMC > 90 and tau0lepMMC < 190):
                fillHistograms(taus_p4[0], leptons_p4[(negIndex + 1)%3], leptons_p4[negIndex],
                              leptons_p4[(negIndex - 1)%3], met_p4.Pt(), nJets30, tau0lepMMC, wTotal,
                              nTuples3Lep, newTree3Lep, triLepHistograms)
            else:
              fillHistograms(taus_p4[0], leptons_p4[(negIndex + 1)%3], leptons_p4[negIndex],
                              leptons_p4[(negIndex - 1)%3], met_p4.Pt(), nJets30, tau0lepMMC, wTotal,
                              nTuples3Lep, newTree3Lep)

  print("2lep selection cut integral yield:", diLepHistograms["tauPtSum"].Integral(0,
    diLepHistograms["tauPtSum"].GetNbinsX() + 1))
  print("3lep selection cut integral yield:", triLepHistograms["tauPtSum"].Integral(0,
    triLepHistograms["tauPtSum"].GetNbinsX() + 1))


  # Write Ntuples to files
  newTree2Lep.Write()
  newTree3Lep.Write()
  outNtupleFile.Close()
  del newTree2Lep
  del newTree3Lep


  # Generates output file name from input file name if not specified
  if (args.outputfile == None):
    outputName = "outputRoot/" + args.inputsample[:-1] + "-weighted.root"
  else:
    if (args.outputfile[-5:] != ".root"): #adds .root to end of output file if not present
      args.outputfile += ".root"
    outputName = "outputRoot/" + args.outputfile

  outHistFile = ROOT.TFile.Open(outputName, "RECREATE")
  outHistFile.cd()
  for key in diLepHistograms: #writes all histograms
    diLepHistograms[key].Write()
    triLepHistograms[key].Write()

  outHistFile.Close()

  del tree

if __name__ == "__main__":
  # parse the CLI arguments
  parser = argparse.ArgumentParser(description='script to run over ntuple dataset')
  parser.add_argument('--inputsample', '-i', metavar='INPUT', type=str, dest="inputsample",
    default="ZHlltt/", help='directory for input root files')
  parser.add_argument('--outputfile', '-o', metavar='OUTPUT', type=str, dest="outputfile",
    default=None, help='outputfile for process')
  parser.add_argument('--ntuplefile', '-n', metavar='NTUPLEOUT', type=str, dest="outputntfile",
    default=None, help='outputfile for ntuple')
  args = parser.parse_args()

  # call the main function
  main(args)