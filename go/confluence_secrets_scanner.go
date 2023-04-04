package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"regexp"
)

const (
	confluenceURL = "https://your-confluence-instance.com"
)

var (
	patterns = []string{
		"[a-zA-Z0-9]{32}",
		"(?i)password\\s*[:=]\\s*[a-zA-Z0-9!@#$%^&*()_+-=]{6,}",
		"Bearer\\s+[a-zA-Z0-9\\-_]+\\.[a-zA-Z0-9\\-_]+\\.[a-zA-Z0-9\\-_]+",
	}
)

type Page struct {
	ID     string `json:"id"`
	Title  string `json:"title"`
	Body   Body   `json:"body"`
}

type Body struct {
	Storage Storage `json:"storage"`
}

type Storage struct {
	Value string `json:"value"`
}

type SearchResult struct {
	Results []Page `json:"results"`
	Size    int    `json:"size"`
}

type SpaceResult struct {
	Results []Space `json:"results"`
	Size    int     `json:"size"`
}

type Space struct {
	Key string `json:"key"`
}

func main() {
	accessToken := os.Getenv("CONFLUENCE_ACCESS_TOKEN")
	client := &http.Client{}

	spaces := getAllSpaces(client, accessToken)
	for _, space := range spaces {
		fmt.Printf("Searching for secrets in space \"%s\"...\n", space.Key)
		searchSpace(space.Key, client, accessToken)
	}

	fmt.Println("Finished searching for secrets.")
}

func getAllSpaces(client *http.Client, accessToken string) []Space {
	var spaces []Space
	start := 0
	limit := 25

	for {
		url := fmt.Sprintf("%s/rest/api/space?start=%d&limit=%d", confluenceURL, start, limit)
		req, _ := http.NewRequest("GET", url, nil)
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", accessToken))

		resp, err := client.Do(req)
		if err != nil {
			fmt.Println("Error fetching spaces:", err)
			os.Exit(1)
		}
		defer resp.Body.Close()

		body, _ := ioutil.ReadAll(resp.Body)

		var spaceResult SpaceResult
		json.Unmarshal(body, &spaceResult)
		spaces = append(spaces, spaceResult.Results...)

		if spaceResult.Size < limit {
			break
		}

		start += limit
	}

	return spaces
}

func searchSpace(spaceKey string, client *http.Client, accessToken string) {
	start := 0
	limit := 25

	for {
		url := fmt.Sprintf("%s/rest/api/content/search?cql=space=%s&start=%d&limit=%d&expand=id", confluenceURL, spaceKey, start, limit)
		req, _ := http.NewRequest("GET", url, nil)
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", accessToken))

		resp, err := client.Do(req)
		if err != nil {
			fmt.Println("Error searching space:", err)
			os.Exit(1)
		}
		defer resp.Body.Close()

		body, _ := ioutil.ReadAll(resp.Body)

		var searchResult SearchResult
		json.Unmarshal(body, &searchResult)

		for _, page := range searchResult.Results {
			searchPage(page.ID, client, accessToken)
		}

		if searchResult.Size < limit {
			break
		}

		start += limit
	}
}

func searchPage(pageID string, client *http.Client, accessToken string) {
	url := fmt.Sprintf("%s/rest/api/content/%s?expand=body.storage", confluenceURL, pageID)
	req, _ := http.NewRequest("GET", url, nil)
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", accessToken))

	resp, err := client.Do(req)
	if err != nil {
		fmt.Println("Error searching page:", err)
		os.Exit(1)
	}
	defer resp.Body.Close()

	body, _ := ioutil.ReadAll(resp.Body)

	var page Page
	json.Unmarshal(body, &page)

	content := page.Body.Storage.Value
	title := page.Title

	foundSecrets := []string{}

	for _, pattern := range patterns {
		re := regexp.MustCompile(pattern)
		matches := re.FindAllString(content, -1)

		if len(matches) > 0 {
			foundSecrets = append(foundSecrets, matches...)
		}
	}

	if len(foundSecrets) > 0 {
		fmt.Printf("Secrets found in \"%s\" (Page ID: %s):\n", title, pageID)
		for _, secret := range foundSecrets {
			fmt.Printf("  - %s\n", secret)
		}
	}
}
