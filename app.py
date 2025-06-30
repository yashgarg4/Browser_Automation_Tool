import asyncio
import pandas as pd
import re
from playwright.async_api import async_playwright, TimeoutError

CRAZY_GAMES_URL = "https://www.crazygames.com/"
OUTPUT_FILE_NAME = "crazygames_data.xlsx"

async def get_game_details(page, game_name: str) -> dict:
    print(f"  - Searching for game: '{game_name}'...")
    try:
        await page.fill("#search-input", game_name)
        await page.press("#search-input", "Enter")
        await page.wait_for_load_state('networkidle')

        first_card = page.locator("div.css-1uvr28v a").first
        await first_card.wait_for(state="visible", timeout=10000)
        await first_card.click()
        await page.wait_for_load_state('networkidle')
        print(f"  - Opened first result for '{game_name}'")

        details = {
            "Game Name": "N/A",
            "Game URL": page.url,
            "Developer": "N/A",
            "Rating": "N/A",
            "Votes": "N/A",
            "Platform": "N/A",
        }

        # Get game name if available
        try:
            details["Game Name"] = await page.locator("h1").inner_text()
        except:
            print("    - Game name not found.")

        # Get all text blocks that contain a colon (e.g., "Developer:", "Rating:", etc.)
        await page.wait_for_selector("div.GameSummary_gameTableRow__9i4Mt", timeout=10000)
        info_blocks = page.locator("div.GameSummary_gameTableRow__9i4Mt") 
        count = await info_blocks.count()

        for i in range(count):
            text = await info_blocks.nth(i).inner_text()

            if text.startswith("Developer:"):
                details["Developer"] = text.replace("Developer:", "").strip()

            elif text.startswith("Rating:"):
                rating_match = re.search(r"(\d+(\.\d+)?)\s+\(([\d,]+)\s+votes\)", text)
                if rating_match:
                    details["Rating"] = rating_match.group(1)
                    details["Votes"] = rating_match.group(3)
                else:
                    details["Rating"] = text.replace("Rating:", "").strip()

            # elif "Platform:" in text:
            #     details["Platform"] = text.replace("Platform:", "").strip()
            elif True:
                text = await info_blocks.nth(i).locator("div").nth(0).inner_text()
                if "Platform" in text:
                    value = await info_blocks.nth(i).locator("div").nth(1).inner_text()
                    details["Platform"] = value.strip()

        return details

    except Exception as e:
        print(f"  - Error processing '{game_name}': {e}")
        return {
            "Game Name": f"{game_name} (Error)",
            "Game URL": "N/A",
            "Developer": "N/A",
            "Rating": "N/A",
            "Votes": "N/A",
            "Platform": "N/A",
        }

async def main():
    """
    Main function to orchestrate the web scraping workflow.
    """
    # Step 3 (Part 1): Get genre input from the user
    genre = input("Please enter the game genre you want to search for (e.g., Action, Puzzle, Racing): ")
    if not genre:
        print("Genre cannot be empty. Exiting.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            # Step 1 & 2: Directly navigate to CrazyGames.com
            print("Step 1 & 2: Directly navigating to CrazyGames.com...")
            await page.goto(CRAZY_GAMES_URL)
            await page.wait_for_load_state('networkidle')
            print(" -> Successfully landed on CrazyGames.com")

            # Step 3 (Part 2): Search for the specified genre on CrazyGames and navigate to the genre page
            print(f"\nStep 3: Searching for genre: '{genre}'...")
            await page.fill("#search-input", genre)
            await page.press("#search-input", "Enter")
            await page.wait_for_load_state('networkidle')
            print(f" -> Loaded search results for '{genre}'.")

            # Strategy: First, try to click a dedicated genre page link.
            # If that fails, fall back to clicking the first game card.
            navigation_successful = False
            try:
                # Look for a link that explicitly matches the genre name (case-insensitive)
                # Using get_by_role("link") with a regex for flexibility.
                # Added (\\s+Games)? to handle cases like "Action" vs "Action Games"
                genre_link_locator = page.get_by_role("link", name=re.compile(rf"^{re.escape(genre)}(\s+Games)?$", re.IGNORECASE)).first
                await genre_link_locator.click(timeout=5000) 
                await page.wait_for_load_state('networkidle')
                print(f" -> Successfully navigated to the dedicated '{genre}' genre page.")
                navigation_successful = True
            except TimeoutError:
                print(f" -> Dedicated '{genre}' genre page link not found. Falling back to clicking a game card.")
                pass # Continue to the next try block if this fails

            if not navigation_successful:
                try:
                    # If no dedicated genre page, click the first game card to get to a game page
                    first_game_card_link_locator = page.locator("div.css-1uvr28v").first
                    await first_game_card_link_locator.click(timeout=10000)
                    await page.wait_for_load_state('networkidle')
                    print(" -> Successfully navigated to a game page to find the FAQ.")
                    navigation_successful = True
                except TimeoutError:
                    print(" -> Could not find or click any game link on the genre search results page. Exiting.")
                    return

            if not navigation_successful:
                return

            # Step 4: Scroll down and find the FAQ section to extract game names
            print("\nStep 4: Locating FAQ section and extracting popular game names...")
            faq_question_text = f"What are the most popular {genre.capitalize()} Games?"
            game_names = []
            try:
                faq_question_locator = page.get_by_role("heading", name=faq_question_text)
                # Explicitly wait for the FAQ question to be visible before scrolling or extracting
                await faq_question_locator.wait_for(state='visible', timeout=10000)
                await faq_question_locator.scroll_into_view_if_needed() # Ensure it's in view
                print(f" -> Found FAQ question: '{faq_question_text}'")
                # Now find the list of games in the FAQ section
                answer_list_locator = faq_question_locator.locator("xpath=./following::ol | ./following::ul").first
                await answer_list_locator.wait_for(state='visible', timeout=5000)
                
                # Get all list items (li) within that list
                list_items_raw_texts = await answer_list_locator.locator("li").all_inner_texts()
                
                for item_text in list_items_raw_texts:
                    # Remove any leading number like "1. " or "2." and strip whitespace
                    cleaned_item_text = re.sub(r'^\s*\d+\.\s*', '', item_text).strip()
                    if cleaned_item_text:
                        game_names.append(cleaned_item_text)

                print(f" -> Raw FAQ list items extracted: {list_items_raw_texts}") 
            except Exception as e:
                print(f" -> An unexpected error occurred during FAQ extraction: {e}. Exiting.")
                return

            # Ensure unique game names and limit to 10
            game_names = list(dict.fromkeys(game_names)) # Remove duplicates while preserving order
            game_names = game_names[:10] # Limit to 10 games as per requirement
            
            if not game_names:
                print(" -> Could not find any game names in the FAQ section. Exiting.")
                return
            
            print(f" -> Final list of games to scrape: {game_names}")

            # Step 5 & 6: Iterate through each game, extract details
            print("\nStep 5 & 6: Scraping details for each game...")
            all_game_data = []
            for game_name in game_names:
                await page.goto(CRAZY_GAMES_URL)
                await page.wait_for_load_state('networkidle')
                
                game_data = await get_game_details(page, game_name)
                all_game_data.append(game_data)
                print(f"  -> Scraped: {game_data}")

            # Step 7: Save all extracted data to an Excel file
            print(f"\nStep 7: Saving data to '{OUTPUT_FILE_NAME}'...")
            df = pd.DataFrame(all_game_data)
            df.to_excel(OUTPUT_FILE_NAME, index=False, engine='openpyxl')
            print(" -> Done! Your file has been saved successfully.")

        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())