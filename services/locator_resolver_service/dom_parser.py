from bs4 import BeautifulSoup, Tag, Comment
import re
from .scorer import LocatorScorer
from .signature_generator import SignatureGenerator

class DomParser:
    IMPORTANT_TAGS = {
        'div', 'span', 'a', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'section', 'select', 'option', 'input', 'button', 'form',
        'label', 'textarea', 'img', 'nav', 'ul', 'ol', 'li',
        'table', 'tr', 'td', 'th', 'thead', 'tbody',
        'main', 'article', 'aside', 'header', 'footer',
        'iframe', 'canvas', 'video', 'audio'
    }


# try to call this method before cleaning up the dom - cause there are instance where the xpath generated will be invalid due to missing strucure 
    @staticmethod
    def get_xpath(element):
        components = []
        child = element
        while child and child.parent:
            siblings = child.parent.find_all(child.name, recursive=False)
            if len(siblings) > 1:
                count = 1
                for sibling in siblings:
                    if sibling is child:
                        components.append(f'{child.name}[{count}]')
                        break
                    count += 1
            else:
                components.append(child.name)

            if child.name == 'body':
                break
            child = child.parent

        components.reverse()
        return '/' + '/'.join(components)

    @staticmethod
    def generate_locators(element, xpath):
        locators = []
        tag = element.name
        attrs = element.attrs
        direct_text = ''.join(t for t in element.contents if isinstance(t, str)).strip()
        text = re.sub(r'\s+', ' ', direct_text).strip()

        role = attrs.get('role', tag)
        name = attrs.get('aria-label', text)

        if role in ['button', 'link', 'heading', 'checkbox', 'radio', 'textbox', 'listitem', 'menu', 'menuitem', 'tab', 'tabpanel', 'dialog'] and name:
            locator_string = f'page.get_by_role("{role}", {{ name: "{name}" }})'
            score = LocatorScorer.score_locator("get_by_role", locator_string, attrs, text)
            locators.append({"type": "get_by_role", "locator": locator_string, "score": score})

        if 'aria-label' in attrs:
            label = attrs['aria-label']
            locator_string = f'page.get_by_label("{label}")'
            score = LocatorScorer.score_locator("get_by_label", locator_string, attrs, text)
            locators.append({"type": "get_by_label", "locator": locator_string, "score": score})

        if direct_text:
            exact = ", { exact: true }" if len(direct_text) < 30 else ""
            locator_string = f'page.get_by_text("{direct_text}"{exact})'
            score = LocatorScorer.score_locator("get_by_text", locator_string, attrs, direct_text)
            locators.append({"type": "get_by_text", "locator": locator_string, "score": score})

        css_selector = tag
        locator_type = "css"
        if 'id' in attrs:
            css_selector = f"#{attrs['id']}"
            locator_type = "id"
        elif 'class' in attrs and attrs['class']:
            css_selector = f"{tag}.{'.'.join(attrs['class'])}"

        if css_selector != tag:
            locator_string = f'page.locator("{css_selector}")'
            score = LocatorScorer.score_locator(locator_type, locator_string, attrs, text)
            locators.append({"type": locator_type, "locator": locator_string, "score": score})

        if xpath:
            locator_string = f'page.locator("{xpath}")'
            score = LocatorScorer.score_locator("xpath", locator_string, attrs, text)
            locators.append({"type": "xpath", "locator": locator_string, "score": score})

        return locators

    @staticmethod
    def to_tree(element):
        if not hasattr(element, 'name') or element.name is None:
            return None
        if element.name not in DomParser.IMPORTANT_TAGS:
            return None

        direct_text = ""
        for content in element.contents:
            if isinstance(content, str):
                text = content.strip()
                if text:
                    direct_text += text + " "
        direct_text = direct_text.strip()

        return {
            "tag": element.name,
            "attributes": dict(element.attrs),
            "innerText": direct_text,
            "children": [child for child in (DomParser.to_tree(c) for c in element.children) if child]
        }

    @staticmethod
    def clean_dom_new(soup):
        # Step 1: Perform initial cleaning (same as original clean_dom)
        for tag in ["head", "script", "style", "link", "meta", "noscript", "template"]:
            for match in soup.find_all(tag):
                match.decompose()

        def is_hidden(tag):
            style = tag.attrs.get("style", "")
            if isinstance(style, list):
                style = " ".join(style)
            if re.search(r"display\s*:\s*none", style, re.IGNORECASE):
                return True
            if "hidden" in tag.attrs:
                return True
            return False

        tags_to_remove = set()
        for tag in soup.find_all(True):
            current = tag
            while current and isinstance(current, Tag):
                if is_hidden(current):
                    tags_to_remove.add(tag)
                    break
                current = current.parent
        for tag in tags_to_remove:
            if not tag.decomposed:
                tag.decompose()

        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        allowed_attrs = {"id", "class", "name", "type", "value", "aria-label", "aria-labelledby", "role", "placeholder", "href", "alt", "title"}
        for tag in soup.find_all(True):
            if isinstance(tag, Tag):
                attrs_to_remove = [attr for attr in tag.attrs if attr not in allowed_attrs]
                for attr in attrs_to_remove:
                    del tag.attrs[attr]

        # Step 2: Apply new relevancy-based filtering using a robust bottom-up approach
        interactive_tags = {'a', 'button', 'input', 'select', 'textarea', 'option', 'label'}
        identifying_attrs = {'id', 'name', 'aria-label', 'aria-labelledby', 'placeholder'} # role is often used for structure

        # Get all elements and reverse them to process from the leaves up to the root
        all_elements = soup.find_all(True)
        all_elements.reverse()

        for element in all_elements:
            if not isinstance(element, Tag) or not element.parent:
                continue

            is_interactive = element.name in interactive_tags or element.attrs.get('role') in ['button', 'link', 'checkbox', 'radio', 'textbox']
            has_identifying_attrs = any(attr in element.attrs for attr in identifying_attrs)
            has_meaningful_text = any(isinstance(c, str) and c.strip() for c in element.contents)
            
            # Check if the element has any children that are tags
            has_tag_children = element.find(True, recursive=False) is not None

            # If the element is meaningful by itself, we keep it and continue
            if is_interactive or has_identifying_attrs or has_meaningful_text:
                continue

            # If it's not meaningful by itself but has children, we also keep it.
            # Since we are processing bottom-up, any non-meaningful children would have
            # already been removed. If it still has children, they are important.
            if has_tag_children:
                continue

            # If we reach here, the element is not meaningful and has no meaningful children left.
            element.decompose()
            
        return soup

    @staticmethod
    def to_flat_list(soup):
        elements = []
        
        # First, generate XPaths for all elements before cleaning
        # We need to do this because cleaning might remove elements that affect XPath generation
        xpath_cache = {}
        
        def cache_xpaths(el):
            if hasattr(el, 'name') and el.name is not None:
                if el.name in DomParser.IMPORTANT_TAGS:
                    xpath_cache[el] = DomParser.get_xpath(el)
                for child in el.children:
                    if isinstance(child, Tag):
                        cache_xpaths(child)
        
        # Cache XPaths for all important elements
        cache_xpaths(soup)
        
        # Now clean the DOM
        cleaned_soup = DomParser.clean_dom_new(soup)

        def walk(el):
            if hasattr(el, 'name') and el.name is not None:
                if el.name in DomParser.IMPORTANT_TAGS:
                    # Generate signature first
                    signature = SignatureGenerator.generate_signature(el)
                    
                    # Only include elements with meaningful signatures
                    if signature:
                        # Use cached XPath if available, otherwise generate new one
                        xpath = xpath_cache.get(el, DomParser.get_xpath(el))
                        locators = DomParser.generate_locators(el, xpath)
                        sorted_locators = sorted(locators, key=lambda x: x["score"], reverse=True)

                        elements.append({
                            "signature": signature,
                            "locators": sorted_locators,
                        })

                for child in el.children:
                    if isinstance(child, Tag):
                        walk(child)

        walk(cleaned_soup)
        return elements