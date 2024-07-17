# Import packages
import streamlit as st
import pandas as pd
from io import BytesIO
import requests

#Start
# Initialize the app
monsterdata = pd.read_csv('pf2_monster_data.csv')
encounter_budget = pd.read_parquet('encounter_budget.parquet')

for i in range(1, 3):
    monsterdata.loc[monsterdata[f'Reaction {i}'].str.contains('Attack of Opportunity', na=False), f'Reaction {i}'] = 'Attack of Opportunity'

st.title('Encounter Builder')
st.write('This is a simple encounter builder for Pathfinder 2e. It is based on the encounter budget system in the Gamemastery Guide.')

# Sidebar

# Encounter Budget
with st.form('creation_form'):
    st.sidebar.title('Party Level')

    party_level = st.sidebar.slider('Select Party Level', 1, 20, 5)

    st.sidebar.title('Encounter Budget')
    budget_name = st.sidebar.selectbox('Select Encounter Budget', encounter_budget['budget_name'], index= 2)
    budget = encounter_budget.loc[encounter_budget['budget_name'] == budget_name, 'budget_value'].values[0]

    trait = st.sidebar.selectbox('Select Trait', sorted(monsterdata['Trait 1'].unique()))
    st.sidebar.write(f'Your budget is {budget} XP.')

    monsterdata_filtered = monsterdata[monsterdata['Creature Level'].isin(range(party_level - 4, party_level + 4))]
    monsterdata_filtered = monsterdata_filtered[monsterdata_filtered['Trait 1'].isin([trait])]

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

    
    submit_button = st.form_submit_button('Create Encounter')

    if submit_button:
        encounter = encounter_basic(budget_name)
        encounter['Traits'] = encounter['Trait 1'] + ' | ' + encounter['Trait 2'].fillna('') + ' | ' + encounter['Trait 3'].fillna('')
        encounter['Perception'] =  encounter['Perception'].astype(str) + '; ' + encounter['Senses'].fillna('').astype(str)

        for i in range(0, len(encounter.index)):
            
            st.markdown('---')
            st.markdown(f':blue-background[{encounter["name"].iloc[i]}]', help=f'Attack = {encounter["Attack 1"].iloc[i]} | AC = {encounter["AC"].iloc[i]} | HP = {encounter["HP"].iloc[i]} | Perception = {encounter["Perception"].iloc[i]} | Speed = {encounter["Speed"].iloc[i]} | XP = {encounter["exp"].iloc[i]}')
            st.markdown(f'{encounter[["Traits"]].iloc[i][0]}')
            st.markdown(f'**Perception** +{encounter[["Perception"]].iloc[i][0]}')
            st.markdown(f'''**STR** + {encounter["Strength"].iloc[i]} ; 
                            **DEX** + {encounter["Dexterity"].iloc[i]} ; 
                            **CON** + {encounter["Constitution"].iloc[i]} ; 
                            **INT** + {encounter["Intelligence"].iloc[i]} ; 
                            **WIS** + {encounter["Wisdom"].iloc[i]} ; 
                            **CHA** + {encounter["Charisma"].iloc[i]}''')
            
            skill_list = ['Acrobatics', 'Arcana', 'Athletics', 'Crafting', 'Deception', 'Diplomacy', 'Intimidation', 'Medicine', 'Nature', 'Occultism', 'Performance', 'Religion', 'Society', 'Stealth', 'Survival', 'Thievery']
            
            skill_string = ''

            for skill in skill_list:
                if not pd.isna(encounter[skill].iloc[i]):
                    skill_string += f'{skill} +{encounter[skill].iloc[i]} ; '
            st.markdown(f'**Skills** {skill_string}')

            st.slider(f'Damage to {encounter["name"].iloc[i]}', 0, encounter['HP'].iloc[i], 0, key=f'HP_{i}')

            for j in range(1, 7):
                if not pd.isna(encounter[f'Attack {j}'].iloc[i]):
                    st.markdown(f'Attack {j} = {encounter[f"Attack {j}"].iloc[i]}')
