import uproot
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.layers import Dense
from selectionPlots import findAllFilesInPath

zJetsSamples = []
zJetsSamples.extend(findAllFilesInPath("*Zee*.root", "outputRoot/"))
zJetsSamples.extend(findAllFilesInPath("*Zmumu*.root", "outputRoot/"))
zJetsSamples.extend(findAllFilesInPath("*Ztt*.root", "outputRoot/"))

nTupleSamples = ("ggZH", "ZHlltt", "llll", "lllv", "WqqZll", "ZqqZll", "ttH", "llvv")

nTupleSamples = {
  "ggZH": 1,
  "ZHlltt": 1,
  "llll": 0,
  "lllv": 0,
  "WqqZll": 0,
  "ZqqZll": 0,
  "ttH": 0,
  "llvv": 0,
  "ZJets": 0
}


# CHANGE TO SUMMED UP FILE
zhTree2lep = uproot.open("outputNTuples/ZHlltt.root:nominal2lep")
zhTree2lep.show()

X = zhTree2lep.arrays(["tauPtSum", "zMassSum", "metPt", "deltaRll", "deltaRtt", "deltaEtall", "deltaEtatt", "nJets",
                       "deltaPhill", "deltaPhitt", "deltaPhilltt", "mmc"], library = "np")
# print(properties)

zhWeight2lep = zhTree2lep.arrays(["weight"], library = "np") # weight for each event
y = np.ones(len(X)) # 1 for signal, 0 for background

sc = StandardScaler()
X = sc.fit_transform(X) # scale the data
ohe = OneHotEncoder()
y = ohe.fit_transform(y).toarray() # hot encoding labels

# Split the data into training and testing sets
X_train,X_test,y_train,y_test = train_test_split(X,y,test_size = 0.1)

# Create the model
model = Sequential()
model.add(Dense(10, input_dim = 12, activation = "relu")) # Hidden layer with 10 nodes
model.add(Dense(6, activation = "relu")) # Hidden layer with 6 nodes
model.add(Dense(2, activation = "softmax")) # 2 output nodes for 2 classes
model.compile(loss = "categorical_crossentropy", optimizer = "adam", metrics = ["accuracy"]) # Compile the model
