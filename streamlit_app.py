
# import config
import streamlit as st
import pandas as pd
from PIL import Image
# from streamlit_extras.add_vertical_space import add_vertical_space
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode
from datetime import datetime


import requests
import boto3
import json

# # Load API keys from JSON file
# with open('config.json') as file:
#     config = json.load(file)

# # Access the API keys
# aws_access_key_id = config['aws_access_key_id']
# aws_secret_access_key = config['aws_secret_access_key']
# apiKey_spoonacular = config['apiKey_spoonacular']

# change this for running streamlit on cloud
aws_access_key_id = st.secrets["aws_access_key_id"]
aws_secret_access_key = st.secrets["aws_secret_access_key"]
apiKey_spoonacular = st.secrets["apiKey_spoonacular"]


st.title('Welcome to 5 Sec Recipes App! 🍽️🍅🍆🥦')


st.subheader(""" To get the best recipe, please input the following: """)

user_input = st.text_input("📝 Input your ingredients:")

num_recipe_input = st.slider('📝 Input the number of recipe results you want to compare:', 2 ,15) 


if user_input:
  @st.cache_data
  def get_dataframe(user_input, num_recipe_input):
    # Use the inputs to get recipes from API
    input_ingredients = str(user_input) # ['onions', 'beef']
    number_recipe_search = num_recipe_input
    response = requests.get("https://api.spoonacular.com/recipes/findByIngredients?", 
                    params={'apiKey': apiKey_spoonacular , 'ingredients':input_ingredients, 'number':number_recipe_search}).json()

    df = pd.DataFrame(response)

    # Find the recipe ids
    recipe_search_id = df['id']
    recipe_search_id = list(str(x) for x in recipe_search_id)
    recipe_search_id = ','.join(recipe_search_id)

    # Get each of the receipes detail information
    response2 = requests.get("https://api.spoonacular.com/recipes/informationBulk?",params={'apiKey':apiKey_spoonacular ,'ids':recipe_search_id}).json()
    df_info = pd.json_normalize(response2)

    df_info_chosen = df_info[['id','title', 'readyInMinutes','servings','analyzedInstructions',"sourceUrl","pricePerServing","vegetarian","vegan","glutenFree","dairyFree" , "image", 'dishTypes','diets']]

    # Get all the prices
    recipe_prices = df_info_chosen.pricePerServing.values.tolist()
    n_groups = 2  # there will be 3 groups

    # Calculate the range of the prices
    min_price = min(recipe_prices)
    max_price = max(recipe_prices)
    price_range = max_price - min_price

    # Calculate the size of each group's range
    group_range_size = price_range / n_groups

    # Assign an ordinal value to each price based on its position in the price range
    price_to_ordinal = {price: int((price - min_price) // group_range_size) for price in recipe_prices}

    # Create a list of ordinal values in the same order as the original prices
    ordinal_values = [price_to_ordinal[price] for price in recipe_prices]

    # Map ordinal values to symbols
    ordinal_to_symbol = {0: '$', 1: '$$', 2: '$$$', 3: '$$$$'}
    symbol_values = [ordinal_to_symbol[ordinal] for ordinal in ordinal_values]

    df_info_chosen['Relative_Cost'] = symbol_values

    # Combine 2 dataframe
    df_all = df_info_chosen.join(df, lsuffix="_left")
    # df_all = df_info_chosen.merge(df)

    # 'pricePerServing'
    df_all_chosen = df_all[["title","usedIngredientCount","missedIngredientCount",'readyInMinutes','servings','Relative_Cost', "analyzedInstructions", "vegetarian","vegan","glutenFree","dairyFree", "image", 'dishTypes', "usedIngredients","missedIngredients","diets"]]

    df_all_chosen.rename(columns = {'title':'Title', 'usedIngredientCount':'Used_Ingredient_Count','missedIngredientCount':'Needed_Ingredient_Count',
                                    'readyInMinutes': 'Ready_in_Minutes'}, inplace = True)

    st.dataframe(df_all_chosen[["Title","Used_Ingredient_Count","Needed_Ingredient_Count",'Ready_in_Minutes','Relative_Cost',"vegetarian","vegan","glutenFree","dairyFree",'servings','dishTypes',"diets"]])

    return df_all_chosen

  df_all_chosen = get_dataframe(user_input, num_recipe_input)
  

  # Upload dataframe to Amazon S3

  df_all_chosen.to_csv('df_capstone_streamlit.csv')
  session = boto3.session.Session( 
    aws_access_key_id= aws_access_key_id, 
    aws_secret_access_key= aws_secret_access_key,  
    region_name='us-east-1'
  )
  now = datetime.now() # current date and time
  dt = now.strftime("%Y-%m-%d-%H-%M-%S") #store date time in string
  file_time = dt
  s3_resource = session.resource('s3')
  bucket_name = 'de-capstone-fion'
  bucket = s3_resource.Bucket(bucket_name)
  filename = "df_capstone-" + file_time +".csv"
  bucket.upload_file(Filename='df_capstone_streamlit.csv', Key=filename)
  
  # Filtering options - dish types
  st.sidebar.subheader("Choose your dish types:")
  cat_list = ['appetizers', 'condiment' ,'side dish','soup', 'main course', 'snacks', ]

  # Create a checkbox for each category and store the selection status in the val list
  val = [st.sidebar.checkbox(cat, value=True) for cat in cat_list]

  # Filtering options - dist
  st.sidebar.subheader("")
  st.sidebar.subheader("Choose your diet types:")
  cat_diet_list = ['vegetarian', 'vegan', 'gluten free', 'dairy free', ]

  # Create a checkbox for each category and store the selection status in the val list
  val_diet = [st.sidebar.checkbox(cat, value=False) for cat in cat_diet_list]

  # # Drop rows based on the checkbox results
  drop_flag = [False] *len(df_all_chosen) 
  for index, row in df_all_chosen.iterrows():
    # st.write(row['title'])
    for i, cat in enumerate(cat_list):
      
      if not val[i] and cat in row["dishTypes"]:
        drop_flag[index] = True 
        break
      if val[i] and cat in row["dishTypes"]:
         drop_flag[index] = False
         break 

    for i, cat in enumerate(cat_diet_list):
      #if val_diet[i] and cat in row["diets"]:
        #drop_flag[index] = False
        #break       
      #if not val_diet[i] and cat in row["diets"]:
        #pass
      if val_diet[i] and cat not in row["diets"]:
        drop_flag[index] = True
        break 

  for index, row in df_all_chosen.iterrows():
    if drop_flag[index]: 
        df_all_chosen.drop(index, inplace=True)



  serving_size_input = st.text_input("📝 Input your ideal serving size")

  st.markdown("Please click on the recipe row for more details:")

  select_df = df_all_chosen[["Title","Used_Ingredient_Count","Needed_Ingredient_Count",'Ready_in_Minutes','Relative_Cost','usedIngredients', 'missedIngredients','analyzedInstructions']]

  def aggrid_interactive_table(df: pd.DataFrame):
      """Creates an st-aggrid interactive table based on a dataframe.
      Args:
          df (pd.DataFrame): Source dataframe
      Returns:
          dict: The selected row
      """
      options = GridOptionsBuilder.from_dataframe(
          df, enableRowGroup=True, enableValue=True, enablePivot=True
      )

      options.configure_side_bar()

      options.configure_selection("single")
      selection = AgGrid(
          df,
          enable_enterprise_modules=True,
          gridOptions=options.build(),
          update_mode=GridUpdateMode.MODEL_CHANGED,
          allow_unsafe_jscode=True,
      )
      return selection

  selection = aggrid_interactive_table(df= select_df)


  bucket.download_file(Key= filename, Filename='df_capstone_streamlit.csv')
  s3_df = pd.read_csv('df_capstone_streamlit.csv', index_col=0)

  if selection and serving_size_input:

    

    recipe_title = selection["selected_rows"][0]["Title"]
    st.subheader(recipe_title)

    # Use s3 Dataframe for rest of information
    s3_df.set_index("Title", inplace = True)
    selected_row = (s3_df.loc[recipe_title]).to_json()
    selected_row_json = json.loads(selected_row) 

    def serving_scale(serving_size_input, servings):
      scale_factor = float(serving_size_input)/ float(servings)
      return scale_factor
    
    used_ingred = selected_row_json['usedIngredients'].replace("'", "\"") #By replacing the single quotes with double quotes, the JSON strings will be valid, with no decoding error.
    needed_ingred = selected_row_json['missedIngredients'].replace("'", "\"")
    servings = selected_row_json['servings'] 
    
    try:
        used_ingred = json.loads(used_ingred.replace("'", '"'))
    except json.JSONDecodeError as e:
        print("Error decoding used_ingred:", e)
        print("used_ingred:", used_ingred)

    try:
        needed_ingred = json.loads(needed_ingred.replace("'", '"'))
    except json.JSONDecodeError as e:
        print("Error decoding needed_ingred:", e)
        print("needed_ingred:", needed_ingred)

    # Print the ingredient lists
    st.write("👉 Used ingredients: ")   

    # Print the ingredient lists
    st.write("👉 Used ingredients:")
    for item in used_ingred:
        try:
            old_amount = float(item['amount'])
            new_amount = round(old_amount * (serving_scale(float(serving_size_input), float(servings))), 3)
            st.write("- ", new_amount, item['unit'], item['originalName'])
        except (KeyError, TypeError) as e:
            print("Error converting used ingredient amount:", e)
            print("item:", item)

    st.write("👉 Needed ingredients:")
    for item in needed_ingred:
        try:
            old_amount = float(item['amount'])
            new_amount = round(old_amount * (serving_scale(float(serving_size_input), float(servings))), 3)
            st.write("- ", new_amount, item['unit'], item['originalName'])
        except (KeyError, TypeError) as e:
            print("Error converting needed ingredient amount:", e)
            print("item:", item)

    st.write("👉 Cooking Instructions: ")

    recipe_instruction = selected_row_json["analyzedInstructions"].replace("'", "\"") # selection["selected_rows"][0]["analyzedInstructions"]
    recipe_instruction= json.loads(recipe_instruction)

    # Get the instruction steps
    steps = [step['step'] for step in recipe_instruction[0]['steps']]

    # Print the steps
    for count, step in enumerate(steps):
        st.write(count+1,". ", step)
    
    # for user take as input
    st.write("Data Output: ")
#     link = "https://de-capstone-fion.s3.amazonaws.com/"+filename
    st.write("https://de-capstone-fion.s3.amazonaws.com/"+filename)
    st.json(selection["selected_rows"])

    # st.dataframe(df_selected["selected_rows"])

  
