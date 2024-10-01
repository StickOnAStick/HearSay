package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"

	"github.com/joho/godotenv"
	supabase "github.com/supabase-community/supabase-go"
)

type BusinessInfo struct {
	Name        string  `json:"name"`
	Rating      float32 `json:"rating"`
	Num_ratings int     `json:"num_ratings"`
	reviews     []Review
}

type TrainBusinessResponse struct {
	ID string `json:"id"`
	// we don't care for these other values.
	// Name        string  `json:"name"`
	// Rating      float32 `json:"rating"`
	// Num_ratings int     `json:"num_ratings"`
}

type TrainBuisnessUpdate struct {
	Reviews []string `json:"reviews"`
}

type Review struct {
	Username string  `json:"username"`
	Rating   float32 `json:"rating"`
	Text     string  `json:"text"`
	BuisId   string  `json:"busi_id"`
}

type ReviewResponse struct {
	ID     string `json:"id"`
	BuisId string `json:"busi_id"`
}

func UploadResults(buisnesses *[]BusinessInfo, API_URL, API_KEY string) {

	client, err := supabase.NewClient(API_URL, API_KEY, nil)

	if err != nil {
		fmt.Println("ERROR: Could not create supabase client! ")
		panic(err)
	}

	for _, busi := range *buisnesses {

		// Upload Buisness data
		fmt.Println("Uploading buis: ", busi.Name, busi.Num_ratings, busi.Rating, len(busi.reviews))
		data, _, err := client.From("train_business").Insert(busi, false, "", "representation", "").Execute()
		if err != nil {
			fmt.Println("ERROR: failed to upload buisness info for ", busi.Name, "\nERROR: ", err)
			panic(err)
		}

		// Extract the generated uuid from data
		var insertedBuisness []TrainBusinessResponse
		err = json.Unmarshal(data, &insertedBuisness)
		if err != nil {
			fmt.Println("ERROR: Could not unmarshal data")
			panic(err)
		}
		var busi_uuid string = insertedBuisness[0].ID
		fmt.Println("DEBUG: Buis id: ", busi_uuid)

		for _, review := range busi.reviews {
			// Upload every review for that buisness, append the result to the associated train_buisness row.
			review.BuisId = busi_uuid
			data, _, err := client.From("train_review").Insert(review, false, "", "representation", "").Execute()

			if err != nil {
				fmt.Println("ERROR: Could not upload review!")
				panic(err)
			}

			var review_response []ReviewResponse
			err = json.Unmarshal(data, &review_response)
			if err != nil {
				fmt.Println("ERROR: Could not parse review json response!")
				panic(err)
			}
			var review_uuid string = review_response[0].ID
			fmt.Println("DEBUG: Review id: ", review_uuid, review_response[0].BuisId)

			// Connect the parent buisness to the inserted review.
			update_result := client.Rpc("append_review_to_train_business", "", map[string]interface{}{
				"business_id": busi_uuid,
				"review_id":   review_uuid,
			})
			fmt.Printf("DEBUG: Buis %s update result: %s", busi_uuid, update_result)

			if err != nil {
				fmt.Println("ERROR: Could not update parent train_buisness row!")
				panic(err)
			}

		}
	}
	fmt.Println("SUCCESS: Completed adding all reviews to the DB.")
}

func ParseBuisness(input []string) *BusinessInfo {
	// Buisness format: id - name - rating - num_ratings - reviews_ids - img_ids

	var ratings, rat_err = strconv.ParseFloat(strings.TrimSpace(input[2]), 32)
	var numRatings, num_err = strconv.Atoi(strings.TrimSpace(input[3]))

	if rat_err != nil || num_err != nil {
		fmt.Println("ERROR: rating or num_ratings could not be converted, ", rat_err, num_err)

		if rat_err != nil {
			panic(rat_err)
		} else {
			panic(num_err)
		}
	}

	buis := BusinessInfo{
		Name:        input[1],
		Rating:      float32(ratings),
		Num_ratings: numRatings,
		reviews:     []Review{},
	}

	//fmt.Println("DEBUG: Created buisness obj: ", buis)

	return &buis
}

func ParseReview(items []string) Review {
	// Review Format: id - buis_id - username - rating - user_prof_id - text
	//fmt.Println("DEBUG: input ->", items)
	var rating, err = strconv.ParseFloat(strings.TrimSpace(items[3]), 32)

	if err != nil {
		fmt.Println(
			"ERROR: Error processing review for buisness named: ", items[0],
			"\nERROR: Couldn't convert to float: ", items[3],
		)
		panic(err)
	}

	review := Review{
		Username: strings.TrimSpace(items[2]),
		Rating:   float32(rating),
		Text:     strings.TrimSpace(items[5]),
	}

	//fmt.Println(review)

	return review
}

func ParseFile(path string) *[]BusinessInfo {
	file, err := os.Open(path)

	if err != nil {
		fmt.Println("Could not open the file!")
		panic(err)
	}
	// defer the closing of the file when scope is exited.
	defer file.Close()

	scanner := bufio.NewScanner(file)

	for i := 0; i < 2; i++ {
		if !scanner.Scan() {
			if err := scanner.Err(); err != nil {
				fmt.Println("Error reading file: ", err)
			} else {
				fmt.Println("File does not contain enough lines!")
			}
			return nil // exit function.
		}
	}

	var businesses []BusinessInfo
	var currentBusiness *BusinessInfo
	// Buisness format: id - name - rating - num_ratings - reviews_ids - img_ids
	// Review Format: id - buis_id - username - rating - user_prof_id - text
	var num_reviews int = 0
	for scanner.Scan() {
		line := scanner.Text()
		//fmt.Println("DEBUG: Line ", line)
		// Format into distinct itmes:
		items := strings.Split(strings.TrimSpace(line), " - ")
		//fmt.Println("DEBUG: Items post parse", items)

		if _, err := strconv.Atoi(strings.TrimSpace(items[0])); err == nil {
			// Parse and store buisness
			fmt.Println("DEBUG: business items: ", items, "\nDEBUG: RAW line: ", line)
			business := ParseBuisness(items)
			businesses = append(businesses, *business)
			// Move the pointer to the most recent buisness
			currentBusiness = &businesses[len(businesses)-1]
		} else {
			review := ParseReview(items)
			if currentBusiness != nil {
				currentBusiness.reviews = append(currentBusiness.reviews, review)
			}
			num_reviews++
		}
		fmt.Println("DEBUG: Parsed ", len(businesses), " businesses and ", num_reviews, " reviews.")
	}

	return &businesses
}

func main() {
	// Process the text files, obtainin the required data for uploading.
	// Feel free to use a lot of memory
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
	}

	var FILE_PATH string = os.Getenv("FILE_PATH")
	fmt.Println("File path: ", FILE_PATH)

	buisnesses := ParseFile(FILE_PATH)

	if buisnesses == nil {
		fmt.Println("ERROR: No Buisnesses returned from parsing.")
		panic("No businesses returned from parsing.")
	}

	// Upload the results in batches to supabase -- concurrently.
	var API_URL string = os.Getenv("SUPABASE_URL")
	var ANON_KEY string = os.Getenv("SUPABASE_ANON")

	if API_URL == "" || ANON_KEY == "" {
		fmt.Println("ERROR: You didn't set your API keys correctly. Please refer to readme")
		panic("Could not access .env DB keys")
	}

	UploadResults(buisnesses, API_URL, ANON_KEY)

	fmt.Print("Process the text files, batch upload requests complete.")
}
