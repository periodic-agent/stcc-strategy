# (code, name, suit, subtype, sp_traits, reg_traits, other_traits, skills, focus, glory, filename, status, notes)
S='AI-seeded — verify'; U='image unreadable — needs manual entry'; N='needs entry (no image yet)'
TBG = [
 ('2PER02/26','Ambassador Gral','Person','','Tellarite','Ambassador','Attack','','',1,'ambassador-gral.jpg',S,''),
 ('2PER03/26','Ash Tyler','Person','','Human, Klingon','Spy, Starfleet','Attack','','',1,'ash-tyler.jpg',S,''),
 ('2PER04/26','Commander Tysess','Person','','Andorian','Starfleet','','','',1,'commander-tysess.jpg',S,''),
 ('2PER05/26','Degra','Person','','Xindi','Scientist','','','',1,'degra.jpg',S,''),
 ('2PER07/26','Hoshi Sato','Person','','Human','NX-01, Starfleet, Communication','','','',1,'hoshi-sato.jpg',S,'NX-01 = new TBG trait'),
 ('2PER08/26','Jackabog','Person','','Pakled','Shady','','','',1,'jackabog.jpg',S,''),
 ('2PER09/26','Landru','Person','','Synthetic','Shady','','','',1,'landru.jpg',S,'Card text: THIS CARD CANNOT BE PLAYED'),
 ('2PER11/26','Malcolm Reed','Person','','Human','Ops, NX-01, Security, Starfleet','','','',1,'malcolm-reed.jpg',S,''),
 ('2PER12/26','Malik','Person','','Human','Weapon, Augment','Attack','Variable, Variable, Variable','',1,'malik.jpg',S,'Variable = 1 Military per Augment in play, max 3 (passive)'),
 ('2PER13/26','Petra Aberdeen','Person','','Human','Scientist','','Research','',1,'petra-aberdeen.jpg',S,''),
 ('2PER14/26','Phlox','Person','','','NX-01, Doctor','','','',1,'phlox-nx01.jpg',S,'Code has dagger (2PER14/26†) = updated repeat of core Phlox; species traits to verify'),
 ('2PER15/26','President Rillak','Person','','Human, Bajoran, Cardassian','Ambassador','','','',1,'president-rillak.jpg',S,''),
 ('2PER18/26','Sarina Douglas','Person','','Human','Augment','','Any, Any, Any','',1,'sarina-douglas.jpg',S,'3 multicolor icons read as Any; verify'),
 ('2PER19/26','Soji Asha','Person','','Android, Synthetic','','','','Variable','?','soji-asha.jpg',S,'Bottom-right gear+? icon'),
 ('2PER23/26','Thelev','Person','','Orion, Andorian','Spy','','','Variable','?','thelev.jpg',S,'Bottom-right star+? icon'),
 ('2PER24/26','Travis Mayweather','Person','','Human','NX-01, Pilot, Starfleet','','','',1,'travis-mayweather.jpg',S,''),
 ('2PER25/26','Va\'Al Trask','Person','','Andorian','Ops, Weapon, Starfleet','','Military, Military','',1,'vaal-trask.jpg',S,''),
 ('2PER26/26','Vice Admiral Pasalk','Person','','Vulcan','Starfleet','Attack','','',1,'vice-admiral-pasalk.jpg',S,''),
 ('2CAR01/18','Augmentation Plague','Cargo','','Klingon','Augment','Ongoing','','Variable','?','augmentation-plague.jpg',S,'Bottom-right gear+?'),
 ('2CAR04/18','Computer Virus','Cargo','','','Engineer, Communication','Attack, Ongoing','Military','',2,'computer-virus.jpg',S,'Left red shield icon read as Military; verify'),
 ('2CAR05/18','Eva Suits','Cargo','','','Helmet, Starfleet','Ongoing','','',2,'eva-suits.jpg',S,''),
 ('2CAR09/18','Jago\'s Epigenetic Implant','Cargo','','','Doctor, Augment, Business','Ongoing','','',2,'jagos-epigenetic-implant.jpg',S,''),
 ('2CAR12/18','Medical Diagnostic Hat','Cargo','','','Helmet, Doctor','','','',2,'medical-diagnostic-hat.jpg',S,''),
 ('2CAR16/18','Saurian Brandy','Cargo','','Alien','Beverage','','','',2,'saurian-brandy.jpg',S,''),
 ('2CAR18/18','Universal Translator','Cargo','','','Communication','','Research','',2,'universal-translator.jpg',S,''),
 ('','Borg Spatial Trajector','Cargo','','','','','','','','borg-spatial-trajector.jpg',U,'Updated repeat; core version in box1.json (borg-spatial-trajectory)'),
 ('','Lirpa','Cargo','','','','','','','','lirpa.jpg',U,'Updated repeat; core version in box1.json'),
 ('','Phasers','Cargo','','','','','','','','phasers.jpg',U,'Updated repeat; core version in box1.json'),
 ('','Orb of Time','Cargo','','','','','','','','orb-of-time.jpg',U,'Updated repeat; core version in box1.json'),
 ('2CAR?','Kemocite','Cargo','','','','','','','','',N,'Image on BGG CDN only; see tbg-cargo.html'),
 ('2LOC03/20','Argus Array','Location','Starting','','Starfleet, Communication','','Any','','','argus-array.jpg',S,'Left multicolor gear icon read as Any; verify'),
 ('2LOC06/20','Denaxi Depot','Location','Starting','Xindi','Shady, Business','','','',1,'denaxi-depot.jpg',S,''),
 ('2LOC10/20','Tahal-Meeroj','Location','Starting','','Anomaly','','','',3,'tahal-meeroj.jpg',S,''),
 ('2LOC11/20','Azati Prime','Location','Advanced','Xindi','Engineer','','Research, Research, Military','',2,'azati-prime.jpg',S,''),
 ('2LOC12/20','Babel One','Location','Advanced','','Ambassador, Communication','','Influence','',2,'babel-one.jpg',S,''),
 ('2LOC14/20','Khitomer','Location','Advanced','Human, Romulan, Klingon','','','','Influence-Variable','?','khitomer.jpg',S,'Bottom-right handshake+?'),
 ('2LOC?','Cold Station 12','Location','Starting','','','','','','','',N,'Image on BGG CDN only'),
 ('2LOC?','Tanuga IV','Location','','','','','','','','',N,'Image on BGG CDN only'),
 ('2LOC?','Tellar Prime','Location','','','','','','','','',N,'Image on BGG CDN only'),
]
for n in ['Kaelon II Science Ministry','Orion Syndicate','Red Squadron','Salt Vampires','Tellarites','Unimatrix Zero',"Vadic's Splinter Group",'Vidiians']:
    TBG.append(('', n, 'Ally','','','','','','','','',N,'Named in tbg-allies guide'))
for n in ["D'Kora Marauder","D'Var",'Medusan Vessel',"Vor'cha Attack Cruiser",'Xindi-Aquatic Cruiser']:
    TBG.append(('', n, 'Ship','','','','','','','','',N,'Named in tbg-ships guide'))
for n, su in [('Delphic Expanse Sphere','Encounter'),('Gomtuu','Encounter'),('New Federation Applicants','Encounter'),('Species 10-C','Encounter'),('Stone of Gol','Encounter'),('Dilithium Shockwave','Incident'),('Reed Alert','Incident')]:
    TBG.append(('', n, su,'','','','','','','','',N,'Named in tbg-encounters-incidents guide; suit Encounter/Incident to verify'))

SC = [
 ('D\'Erika Tendi','Person'),('Jennifer Sh\'reyan','Person'),('K\'ranch','Person'),('Ma\'ah','Person'),
 ('Parmen','Person'),('Gift Box','Cargo'),('Moopsy','Cargo'),('Protocol 12','Cargo'),
 ('Fesarius','Ship'),('R.I.S. Talvath','Ship'),('Betazed Intelligence','Ally'),('Illyrians','Ally'),
 ('Nova Fleet','Ally'),('Orion','Location:Advanced'),('Krulmuth-B','Location:Starting'),
 ('Ambassador Spock','Person'),('Barry Waddle','Person'),('Chancellor Gowron','Person'),('Chef Riker','Person'),
 ('Ensign Boimler','Person'),('Ensign Mariner','Person'),('Lieutenant Dax','Person'),('The Living Witness','Person'),
]
