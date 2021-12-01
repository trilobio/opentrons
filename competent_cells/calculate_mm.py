def make_gg_rxns(num_rxns,rxn_vol, extra=1.2):
    num_rxns = num_rxns*extra
    '''Calculates the amount of each reagent to add to reach the desired master mix'''
    cutsmart = 1 * num_rxns
    atp = 1 * num_rxns
    ligase = 0.5 * num_rxns
    enzyme = 0.25 * num_rxns
    water = (rxn_vol - ((cutsmart + atp + ligase + enzyme)/num_rxns)) * num_rxns
    master_mix = {'Component':['H2O','Cutsmart','ATP','T4 Ligase','Restriction Enzyme','Total'],
        'Amount':[water,cutsmart,atp,ligase,enzyme,rxn_vol*num_rxns]}
    return master_mix

print(make_gg_rxns(32, 18, extra=1.1))
