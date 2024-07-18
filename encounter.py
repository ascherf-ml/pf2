# Import packages
import streamlit as st
import pandas as pd
from io import BytesIO
import requests

#Start
# Initialize the app
monsterdata = pd.read_parquet('pf2_monster_data.parquet')
encounter_budget = pd.read_parquet('encounter_budget.parquet')

for i in range(1, 3):
    monsterdata.loc[monsterdata[f'Reaction {i}'].str.contains('Attack of Opportunity', na=False), f'Reaction {i}'] = 'Attack of Opportunity'

st.title('Encounter Builder')
st.write('This is a simple encounter builder for Pathfinder 2e. It is based on the encounter budget system in the Gamemastery Guide.')

# Sidebar


#with st.form('creation_form'):
# Encounter Budget
    
        

with st.sidebar.form('creation_form'):
    
    st.sidebar.title('Party Level')

    party_level = st.sidebar.slider('Select Party Level', 1, 20, 5)

    st.sidebar.title('Encounter Budget')
    budget_name = st.sidebar.selectbox('Select Encounter Difficulty', encounter_budget['budget_name'], index= 2)
    budget = encounter_budget.loc[encounter_budget['budget_name'] == budget_name, 'budget_value'].values[0]

    trait = st.sidebar.selectbox('Select Trait', sorted(monsterdata[['Trait 1', 'Trait 2', 'Trait 3']].stack().unique()), index=None)
    st.sidebar.write(f'Your budget is {budget} XP.')

    submit_button = st.form_submit_button('Create Encounter')

monsterdata_filtered = monsterdata[monsterdata['Creature Level'].isin(range(party_level - 4, party_level + 4))]
if trait != None:
    monsterdata_filtered = monsterdata_filtered[monsterdata_filtered[['Trait 1', 'Trait 2', 'Trait 3']].isin([trait]).any(axis=1)]

encounter_roles = {'role': ['lackey_low', 'lackey_lowmod', 'lackey', 'standard', 'standard2',
                            'standard3', 'boss_low', 'boss_lowmod', 'boss_modhard','boss_hardextr', 'boss_extreme'], 
                            'creature_level' : [party_level - 4, party_level - 3, party_level - 2, party_level - 2, party_level - 1, party_level,
                                        party_level, party_level + 1, party_level + 2, party_level + 3, party_level + 4],
                    'exp' : [ 10, 15, 20, 20, 30, 40, 40, 60, 80, 120, 160]}
monster_comb = monsterdata_filtered.merge(pd.DataFrame(encounter_roles), left_on='Creature Level', right_on='creature_level')

def create_encounter(encounter_difficulty):
    encounter = []
    sumexp = 0
    for monster in monster_comb.sample(frac=1).iterrows():
        while (sumexp + monster[1]['exp']) <= encounter_budget.loc[encounter_budget['budget_name'] == encounter_difficulty, 'budget_value'].values[0]:
            sumexp += monster[1]['exp']
            encounter.append(monster[1])
            if sumexp == encounter_budget['budget_value'][0]:
                break
    encounter = pd.DataFrame(encounter)
    return encounter

def encounter_basic(budget_level):
    encounter = create_encounter(budget_level)
    #encounter = encounter.dropna(axis=1, how='all')
    return encounter




if submit_button:
    encounter = encounter_basic(budget_name)
    encounter['Traits'] = encounter['Trait 1'] + ' | ' \
                        + encounter['Trait 2'].fillna('') + ' | ' \
                        + encounter['Trait 3'].fillna('')
    encounter['Perception'] =  encounter['Perception'].astype(str) + '; ' + encounter['Senses'].fillna('').astype(str)


    for i in range(0, len(encounter.index)):
        
        st.markdown('---')
        st.markdown(f':blue-background[{encounter["name"].iloc[i]}]')
        st.markdown(f'{encounter[["Traits"]].iloc[i][0]}')
        st.markdown(f'**Perception** +{encounter[["Perception"]].iloc[i][0]}')
        st.markdown(f'''
                    **STR** + {encounter["Strength"].iloc[i]} ; 
                    **DEX** + {encounter["Dexterity"].iloc[i]} ; 
                    **CON** + {encounter["Constitution"].iloc[i]} ; 
                    **INT** + {encounter["Intelligence"].iloc[i]} ; 
                    **WIS** + {encounter["Wisdom"].iloc[i]} ; 
                    **CHA** + {encounter["Charisma"].iloc[i]}
                    ''')
        
        skill_list = ['Acrobatics', 'Arcana', 'Athletics', 
                        'Crafting', 'Deception', 'Diplomacy', 
                        'Intimidation', 'Medicine', 'Nature', 
                        'Occultism', 'Performance', 'Religion', 
                        'Society', 'Stealth', 'Survival', 'Thievery']
        
        skill_string = ''

        for skill in skill_list:
            if not pd.isna(encounter[skill].iloc[i]):
                skill_string += f'{skill} +{encounter[skill].iloc[i]} ; '
        st.markdown(f'**Skills** {skill_string}')

        st.markdown(f''' 
                    **HP** {encounter["HP"].iloc[i]}; 
                    **AC** {encounter["AC"].iloc[i]}; 
                    **Fortitude** +{encounter["Fort"].iloc[i]}; 
                    **Reflex** +{encounter["Ref"].iloc[i]}; 
                    **Will** +{encounter["Will"].iloc[i]}
                    ''')
        #st.slider(f'Damage to {encounter["name"].iloc[i]}', 0, encounter['HP'].iloc[i], 0, key=f'HP_{i}')
        #foe_hp = st.number_input(f'Current HP of {encounter["name"].iloc[i]}', 0, key=f'HHP_{i}')

        attack_expander = st.expander(label = 'Attacks')
        with attack_expander:
            for j in range(1, 7):
                if not pd.isna(encounter[f'Attack {j}'].iloc[i]):
                    st.markdown(f'Attack {j} = {encounter[f"Attack {j}"].iloc[i]}')
        
        if not pd.isna(encounter['Spells 1'].iloc[i]):
            spells_expander = st.expander(label = 'Spells')
            st.markdown(encounter['Spells 1'].iloc[i])
            with spells_expander:
                if not pd.isna(encounter[f'DC'].iloc[i]) and pd.isna(encounter[f'Spell Attack'].iloc[i]):
                    st.markdown(f'{encounter[["Magic School"]].iloc[i][0]}')
                    st.markdown(f'Spell DC: {encounter[["DC"]].iloc[i][0]}')

                    if not pd.isna(encounter[f'Cantrips'].iloc[i]):
                        st.markdown(f'Cantrips: {encounter[["Cantrips"]].iloc[i][0]}')
                    if not pd.isna(encounter[f'Spell Level 1'].iloc[i]):
                        st.markdown(f'1st Level Spells: {encounter[["Spell Level 1"]].iloc[i][0]}')                      
                    if not pd.isna(encounter[f'Spell Level 2'].iloc[i]):
                        st.markdown(f'2nd Level Spells: {encounter[["Spell Level 2"]].iloc[i][0]}')                        
                    if not pd.isna(encounter[f'Spell Level 3'].iloc[i]):
                        st.markdown(f'3rd Level Spells: {encounter[["Spell Level 3"]].iloc[i][0]}')                        
                    if not pd.isna(encounter[f'Spell Level 4'].iloc[i]):
                        st.markdown(f'4th Level Spells: {encounter[["Spell Level 4"]].iloc[i][0]}')                        
                    if not pd.isna(encounter[f'Spell Level 5'].iloc[i]):
                        st.markdown(f'5th Level Spells: {encounter[["Spell Level 5"]].iloc[i][0]}')                        
                    if not pd.isna(encounter[f'Spell Level 6'].iloc[i]):
                        st.markdown(f'6th Level Spells: {encounter[["Spell Level 6"]].iloc[i][0]}')                        
                    if not pd.isna(encounter[f'Spell Level 7'].iloc[i]):
                        st.markdown(f'7th Level Spells: {encounter[["Spell Level 7"]].iloc[i][0]}')                        
                    if not pd.isna(encounter[f'Spell Level 8'].iloc[i]):
                        st.markdown(f'8th Level Spells: {encounter[["Spell Level 8"]].iloc[i][0]}')                        
                    if not pd.isna(encounter[f'Spell Level 9'].iloc[i]):
                        st.markdown(f'9th Level Spells: {encounter[["Spell Level 9"]].iloc[i][0]}')

                else:
                    if not pd.isna(encounter[f'Spell Attack'].iloc[i]):
                        st.markdown(f'{encounter[["Magic School"]].iloc[i][0]}')
                        st.markdown(f'Spell DC: {encounter[["DC"]].iloc[i][0]}; Spell Attack: +{encounter[["Spell Attack"]].iloc[i][0]}')
                        if not pd.isna(encounter[f'Cantrips'].iloc[i]):
                            st.markdown(f'Cantrips: {encounter[["Cantrips"]].iloc[i][0]}')
                        if not pd.isna(encounter[f'Spell Level 1'].iloc[i]):
                            st.markdown(f'1st Level Spells: {encounter[["Spell Level 1"]].iloc[i][0]}')                      
                        if not pd.isna(encounter[f'Spell Level 2'].iloc[i]):
                            st.markdown(f'2nd Level Spells: {encounter[["Spell Level 2"]].iloc[i][0]}')                        
                        if not pd.isna(encounter[f'Spell Level 3'].iloc[i]):
                            st.markdown(f'3rd Level Spells: {encounter[["Spell Level 3"]].iloc[i][0]}')                        
                        if not pd.isna(encounter[f'Spell Level 4'].iloc[i]):
                            st.markdown(f'4th Level Spells: {encounter[["Spell Level 4"]].iloc[i][0]}')                        
                        if not pd.isna(encounter[f'Spell Level 5'].iloc[i]):
                            st.markdown(f'5th Level Spells: {encounter[["Spell Level 5"]].iloc[i][0]}')                        
                        if not pd.isna(encounter[f'Spell Level 6'].iloc[i]):
                            st.markdown(f'6th Level Spells: {encounter[["Spell Level 6"]].iloc[i][0]}')                        
                        if not pd.isna(encounter[f'Spell Level 7'].iloc[i]):
                            st.markdown(f'7th Level Spells: {encounter[["Spell Level 7"]].iloc[i][0]}')                        
                        if not pd.isna(encounter[f'Spell Level 8'].iloc[i]):
                            st.markdown(f'8th Level Spells: {encounter[["Spell Level 8"]].iloc[i][0]}')                        
                        if not pd.isna(encounter[f'Spell Level 9'].iloc[i]):
                            st.markdown(f'9th Level Spells: {encounter[["Spell Level 9"]].iloc[i][0]}')