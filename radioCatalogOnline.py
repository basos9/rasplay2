import controller
from pyradios import RadioBrowser, RadioFacets
from typing import Dict, List, Set, Tuple
import itertools
from radioCatalog import RadioCatalog

class RadioCatalogOnline(RadioCatalog):
    """
    A controller to build radio station menus using the pyradios library.
    With dynamic genre AND country discovery from the Radio Browser API.
    """
    
    def __init__(self):
        # Initialize the main client
        self.rb = RadioBrowser()
        # Initialize the faceted search helper for filtered queries
        self.base_facets = RadioFacets(self.rb)
        # Caches for API data
        self._all_tags_cache = None
        self._all_countries_cache = None

    def _format_station_list(self, stations: List[Dict], limit: int = 15) -> Dict[str, str]:
        """Helper to convert a list of station dicts into the {name: url} format."""
        formatted = {}
        for station in itertools.islice(stations, limit):
            name = station.get('name')
            url = station.get('url')
            if name and url:
                formatted[name] = url
        return formatted

    # ===== GENRE METHODS =====
    def get_all_available_tags(self, force_refresh: bool = False) -> List[str]:
        """Fetches ALL available tags/genres from the Radio Browser API."""
        if self._all_tags_cache is None or force_refresh:
            try:
                all_tags = self.rb.tags()
                self._all_tags_cache = [tag['name'] for tag in all_tags]
                print(f"Fetched {len(self._all_tags_cache)} available tags/genres")
            except AttributeError:
                print("Fetching tags from station data (this might take a moment)...")
                all_stations = self.rb.search(limit=5000)
                tags_set = set()
                for station in all_stations:
                    if 'tags' in station and station['tags']:
                        station_tags = [tag.strip() for tag in station['tags'].split(',')]
                        tags_set.update(station_tags)
                self._all_tags_cache = sorted(list(tags_set))
                print(f"Extracted {len(self._all_tags_cache)} unique tags from stations")
        return self._all_tags_cache

    def get_top_genres(self, min_stations: int = 5, max_genres: int = 100) -> List[str]:
        """Get the most popular genres (those with the most stations)."""
        all_tags = self.get_all_available_tags()
        popular_tags = []
        
        print(f"Analyzing popularity of {len(all_tags)} tags...")
        for i, tag in enumerate(all_tags):
            if i % 20 == 0:
                print(f"  Processing tag {i+1}/{len(all_tags)}: {tag}")
            try:
                tag_facets = self.base_facets.narrow(tag=tag)
                station_count = len(tag_facets)
                if station_count >= min_stations:
                    popular_tags.append((tag, station_count))
            except Exception:
                continue
        
        popular_tags.sort(key=lambda x: x[1], reverse=True)
        return [tag for tag, count in popular_tags[:max_genres]]

    # ===== COUNTRY METHODS =====
    def get_all_available_countries(self, force_refresh: bool = False) -> List[Dict]:
        """
        Fetches ALL available countries from the Radio Browser API.
        Returns list of dicts with country info including codes and station counts.
        """
        if self._all_countries_cache is None or force_refresh:
            try:
                # The RadioBrowser API has an endpoint for countries
                all_countries = self.rb.countries()
                self._all_countries_cache = all_countries
                print(f"Fetched {len(self._all_countries_cache)} available countries")
            except AttributeError:
                # Fallback: extract unique countries from station data
                print("Fetching countries from station data...")
                all_stations = self.rb.search(limit=10000)
                countries_set = set()
                countries_info = {}
                
                for station in all_stations:
                    country_code = station.get('countrycode', '').strip()
                    country_name = station.get('country', '').strip()
                    
                    if country_code and country_code not in countries_set:
                        countries_set.add(country_code)
                        countries_info[country_code] = {
                            'name': country_name or country_code,
                            'countrycode': country_code,
                            'stationcount': 0
                        }
                    if country_code in countries_info:
                        countries_info[country_code]['stationcount'] += 1
                
                self._all_countries_cache = list(countries_info.values())
                print(f"Extracted {len(self._all_countries_cache)} unique countries")
        
        return self._all_countries_cache

    def get_top_countries(self, min_stations: int = 5, max_countries: int = 50) -> List[Tuple[str, str, int]]:
        """
        Get the countries with the most stations.
        Returns list of tuples: (country_code, country_name, station_count)
        """
        all_countries = self.get_all_available_countries()
        
        # Filter by minimum stations and extract relevant info
        valid_countries = []
        for country in all_countries:
            station_count = country.get('stationcount', 0)
            country_code = country.get('countrycode', '')
            country_name = country.get('name', country_code)
            
            if station_count >= min_stations and country_code:
                valid_countries.append((country_code, country_name, station_count))
        
        # Sort by station count (most popular first)
        valid_countries.sort(key=lambda x: x[2], reverse=True)
        
        print(f"Found {len(valid_countries)} countries with at least {min_stations} stations")
        return valid_countries[:max_countries]

    # ===== MENU CREATION METHODS =====
    def create_genre_menu(self, 
                         predefined_genres: List[str] = ["classical", "rock", "pop", "jazz", "electronic"],
                         include_all_genres: bool = True,
                         max_additional_genres: int = 20,
                         limit_per_genre: int = 10) -> Dict[str, Dict[str, str]]:
        """Creates a menu section grouped by music genres."""
        menu = {}
        
        # Process predefined genres first
        print("Processing predefined genres...")
        for genre in predefined_genres:
            try:
                genre_facets = self.base_facets.narrow(tag=genre)
                genre_dict = self._format_station_list(genre_facets.result, limit_per_genre)
                if genre_dict:
                    menu[genre] = genre_dict
                    print(f"  ✓ {genre}: {len(genre_dict)} stations")
                else:
                    print(f"  ✗ {genre}: no stations found")
            except Exception as e:
                print(f"  ✗ {genre}: error - {e}")

        # Add dynamically discovered genres
        if include_all_genres:
            print("Discovering additional genres...")
            all_genres = self.get_top_genres(min_stations=3, max_genres=max_additional_genres + len(predefined_genres))
            
            new_genres = [g for g in all_genres if g not in predefined_genres]
            new_genres = new_genres[:max_additional_genres]
            
            print(f"Adding {len(new_genres)} discovered genres...")
            for i, genre in enumerate(new_genres):
                if i % 5 == 0:
                    print(f"  Processing discovered genre {i+1}/{len(new_genres)}: {genre}")
                try:
                    genre_facets = self.base_facets.narrow(tag=genre)
                    genre_dict = self._format_station_list(genre_facets.result, limit_per_genre)
                    if genre_dict:
                        menu[genre] = genre_dict
                except Exception:
                    continue
        
        return menu

    def create_country_menu(self, 
                           predefined_countries: List[str] = ["US", "GB", "DE", "FR", "JP"],
                           include_all_countries: bool = True,
                           max_additional_countries: int = 30,
                           limit_per_country: int = 10) -> Dict[str, Dict[str, str]]:
        """
        Creates a menu section grouped by country.
        
        Args:
            predefined_countries: Your predefined list of country codes (will appear first)
            include_all_countries: Whether to add dynamically discovered countries
            max_additional_countries: Max number of additional countries to include
            limit_per_country: Max stations per country category
        """
        menu = {}
        
        # Country code to full name mapping for better display
        country_names = {
            'US': 'United States', 'GB': 'United Kingdom', 'DE': 'Germany', 
            'FR': 'France', 'JP': 'Japan', 'IT': 'Italy', 'ES': 'Spain',
            'CA': 'Canada', 'AU': 'Australia', 'NL': 'Netherlands',
            'BR': 'Brazil', 'RU': 'Russia', 'IN': 'India', 'CN': 'China',
            'MX': 'Mexico', 'SE': 'Sweden', 'NO': 'Norway', 'DK': 'Denmark',
            'FI': 'Finland', 'BE': 'Belgium', 'AT': 'Austria', 'CH': 'Switzerland',
            'PL': 'Poland', 'CZ': 'Czech Republic', 'PT': 'Portugal', 'GR': 'Greece',
            'IE': 'Ireland', 'NZ': 'New Zealand', 'ZA': 'South Africa', 'AR': 'Argentina'
        }
        
        # 1. Process predefined countries first (in order specified)
        print("Processing predefined countries...")
        for country_code in predefined_countries:
            try:
                country_facets = self.base_facets.narrow(countrycode=country_code)
                country_dict = self._format_station_list(country_facets.result, limit_per_country)
                if country_dict:
                    # Use country name if available, otherwise use code
                    display_name = country_names.get(country_code, country_code)
                    menu_key = f"country_{display_name.lower().replace(' ', '_')}"
                    menu[menu_key] = country_dict
                    print(f"  ✓ {country_code} ({display_name}): {len(country_dict)} stations")
                else:
                    print(f"  ✗ {country_code}: no stations found")
            except Exception as e:
                print(f"  ✗ {country_code}: error - {e}")

        # 2. Add dynamically discovered countries
        if include_all_countries:
            print("Discovering additional countries...")
            top_countries = self.get_top_countries(
                min_stations=3, 
                max_countries=max_additional_countries + len(predefined_countries)
            )
            
            # Filter out already processed countries
            new_countries = [(code, name, count) for code, name, count in top_countries 
                           if code not in predefined_countries]
            new_countries = new_countries[:max_additional_countries]
            
            print(f"Adding {len(new_countries)} discovered countries...")
            for i, (country_code, country_name, station_count) in enumerate(new_countries):
                if i % 5 == 0:
                    print(f"  Processing discovered country {i+1}/{len(new_countries)}: "
                          f"{country_code} ({country_name}) - {station_count} stations")
                
                try:
                    country_facets = self.base_facets.narrow(countrycode=country_code)
                    country_dict = self._format_station_list(country_facets.result, limit_per_country)
                    if country_dict:
                        display_name = country_name or country_code
                        menu_key = f"country_{display_name.lower().replace(' ', '_')}"
                        menu[menu_key] = country_dict
                except Exception:
                    continue
        
        return menu

    def create_most_played_menu(self, limit: int = 25) -> Dict[str, Dict[str, str]]:
        """Creates a 'Most Played' menu section based on click counts."""
        try:
            most_played_stations = self.rb.search(
                order='clickcount', 
                reverse=True, 
                limit=limit + 50
            )
            return {"most_played": self._format_station_list(most_played_stations, limit)}
        except Exception as e:
            print(f"Error creating most played menu: {e}")
            return {}

    def create_language_menu(self, 
                            predefined_languages: List[str] = ["english", "german", "french", "spanish"],
                            include_all_languages: bool = False,  # Often too many languages
                            limit_per_language: int = 10) -> Dict[str, Dict[str, str]]:
        """Creates a menu section grouped by language."""
        menu = {}
        for language in predefined_languages:
            try:
                lang_facets = self.base_facets.narrow(language=language)
                lang_dict = self._format_station_list(lang_facets.result, limit_per_language)
                if lang_dict:
                    menu[f"language_{language}"] = lang_dict
            except Exception as e:
                print(f"Error processing language {language}: {e}")
        return menu

    def build_full_menu(self, 
                       predefined_genres: List[str] = ["classical", "rock", "pop", "jazz", "electronic"],
                       include_all_genres: bool = True,
                       max_additional_genres: int = 15,
                       predefined_countries: List[str] = ["US", "GB", "DE", "FR", "JP"],
                       include_all_countries: bool = True,
                       max_additional_countries: int = 20,
                       languages: List[str] = ["english", "german", "french", "spanish"],
                       limit_per_category: int = 10,
                       most_played_limit: int = 25) -> Dict[str, Dict[str, str]]:
        """
        Assembles the complete menu by combining all categories.
        Predefined items come first, followed by discovered ones.
        """
        full_menu = {}
        
        # 1. Add genre-based lists (predefined first, then discovered)
        print("🎵 Building genre menus...")
        full_menu.update(self.create_genre_menu(
            predefined_genres=predefined_genres,
            include_all_genres=include_all_genres,
            max_additional_genres=max_additional_genres,
            limit_per_genre=limit_per_category
        ))
        
        # 2. Add country-based lists (predefined first, then discovered)
        print("\n🌍 Building country menus...")
        full_menu.update(self.create_country_menu(
            predefined_countries=predefined_countries,
            include_all_countries=include_all_countries,
            max_additional_countries=max_additional_countries,
            limit_per_country=limit_per_category
        ))
        
        # 3. Add most played list
        print("\n📊 Building most played menu...")
        full_menu.update(self.create_most_played_menu(most_played_limit))
        
        # 4. Add language-based lists
        print("\n🗣️ Building language menus...")
        full_menu.update(self.create_language_menu(languages, limit_per_category=limit_per_category))
        
        print(f"\n✅ Complete menu built with {len(full_menu)} categories")
        
        # Print category summary
        genre_cats = [k for k in full_menu if not k.startswith(('country_', 'language_', 'most_played'))]
        country_cats = [k for k in full_menu if k.startswith('country_')]
        lang_cats = [k for k in full_menu if k.startswith('language_')]
        
        print(f"   📻 {len(genre_cats)} genre categories")
        print(f"   🌍 {len(country_cats)} country categories")
        print(f"   🗣️ {len(lang_cats)} language categories")
        if 'most_played' in full_menu:
            print(f"   📊 1 most played category")
        
        return full_menu

    def init(self):
    # Build complete menu with both genres and countries dynamically
        radio_menu = controller.build_full_menu(
            # Predefined genres (will appear first)
            predefined_genres=["rock", "electronic", "jazz", "ambient"],
            include_all_genres=True,
            max_additional_genres=15,  # Add up to 15 more popular genres
            
            # Predefined countries (will appear first)
            predefined_countries=["GR", "GB", "US", "FR", "JP", "IT", "ES"],
            include_all_countries=True,
            max_additional_countries=25,  # Add up to 25 more countries
            
            # Other settings
            languages=["english", "greek", "french"],
            limit_per_category=10,
            most_played_limit=30
        )
    
        # Show summary of what we got
        print("\n" + "="*60)
        print("MENU STRUCTURE SUMMARY")
        print("="*60)
        
        # Group categories by type for better display
        genre_items = []
        country_items = []
        other_items = []
        
        for category, stations in radio_menu.items():
            station_count = len(stations)
            preview = list(stations.keys())[:2]
            preview_str = " • ".join(preview)
            
            if category.startswith('country_'):
                country_items.append((category, station_count, preview_str))
            elif category in ['most_played'] or category.startswith('language_'):
                other_items.append((category, station_count, preview_str))
            else:
                genre_items.append((category, station_count, preview_str))
        
        print("\n🎵 GENRES:")
        for category, count, preview in genre_items[:10]:
            print(f"  {category:<25} ({count} stations) - {preview}")
        if len(genre_items) > 10:
            print(f"  ... and {len(genre_items) - 10} more genre categories")
        
        print("\n🌍 COUNTRIES:")
        for category, count, preview in country_items[:10]:
            print(f"  {category:<25} ({count} stations) - {preview}")
        if len(country_items) > 10:
            print(f"  ... and {len(country_items) - 10} more country categories")
        
        print("\n📊 OTHER:")
        for category, count, preview in other_items:
            print(f"  {category:<25} ({count} stations) - {preview}")