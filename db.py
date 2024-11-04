def calculate_bmr(weight, height, age, gender):
    if gender.lower() == 'male':
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    elif gender.lower() == 'female':
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    else:
        raise ValueError("Invalid gender input. Please enter 'male' or 'female'.")
    return bmr

def calculate_tdee(bmr, activity_level):
    # Activity level multipliers
    activity_multipliers = {
        'sedentary': 1.2,
        'lightly active': 1.375,
        'moderately active': 1.55,
        'very active': 1.725,
        'super active': 1.9
    }
    
    multiplier = activity_multipliers.get(activity_level.lower())
    if multiplier is None:
        raise ValueError("Invalid activity level. Choose from 'sedentary', 'lightly active', 'moderately active', 'very active', 'super active'.")
    
    tdee = bmr * multiplier
    return tdee

def main():
    print("Calorie Needs Calculator")
    weight = float(input("Enter your weight (kg): "))
    height = float(input("Enter your height (cm): "))
    age = int(input("Enter your age: "))
    gender = input("Enter your gender (male/female): ")
    activity_level = input("Enter your activity level (sedentary, lightly active, moderately active, very active, super active): ")
    
    # Calculate BMR
    bmr = calculate_bmr(weight, height, age, gender)
    print(f"Your Basal Metabolic Rate (BMR) is: {bmr:.2f} calories/day")
    
    # Calculate TDEE
    tdee = calculate_tdee(bmr, activity_level)
    print(f"Your Total Daily Energy Expenditure (TDEE) is: {tdee:.2f} calories/day")

if __name__ == "__main__":
    main()
