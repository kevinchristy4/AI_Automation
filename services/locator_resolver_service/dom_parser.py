from bs4 import BeautifulSoup, Tag, Comment
import re
from .scorer import LocatorScorer

class DomParser:
    IMPORTANT_TAGS = {
        'div', 'span', 'a', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'section', 'select', 'option', 'input', 'button', 'form',
        'label', 'textarea', 'img', 'nav', 'ul', 'ol', 'li',
        'table', 'tr', 'td', 'th', 'thead', 'tbody',
        'main', 'article', 'aside', 'header', 'footer',
        'iframe', 'canvas', 'video', 'audio'
    }

    @staticmethod
    def clean_dom(soup):
        for tag in ["head", "script", "style", "link", "meta", "noscript", "template"]:
            for match in soup.find_all(tag):
                match.decompose()
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        allowed_attrs = {"id", "class", "name", "type", "value", "aria-label", "aria-labelledby", "role", "placeholder", "href", "alt", "title"}
        for tag in soup.find_all(True):
            if isinstance(tag, Tag):
                attrs_to_remove = [attr for attr in tag.attrs if attr not in allowed_attrs]
                for attr in attrs_to_remove:
                    del tag.attrs[attr]
        return soup

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
        text = ' '.join(element.stripped_strings)
        text = re.sub(r'\s+', ' ', text).strip()

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

        if text:
            exact = ", {{ exact: true }}" if len(text) < 30 else ""
            locator_string = f'page.get_by_text("{text}"{exact})'
            score = LocatorScorer.score_locator("get_by_text", locator_string, attrs, text)
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
    def to_flat_list(soup):
        elements = []

        def walk(el):
            if hasattr(el, 'name') and el.name is not None:
                if el.name in DomParser.IMPORTANT_TAGS:
                    direct_text = ""
                    for content in el.contents:
                        if isinstance(content, str):
                            text = content.strip()
                            if text:
                                direct_text += text + " "
                    direct_text = direct_text.strip()

                    xpath = DomParser.get_xpath(el)
                    locators = DomParser.generate_locators(el, xpath)
                    best_locator = sorted(locators, key=lambda x: x["score"], reverse=True)[0] if locators else None

                    elements.append({
                        "tag": el.name,
                        "attributes": dict(el.attrs),
                        "innerText": direct_text,
                        "locators": locators,
                        "best_locator": best_locator
                    })

                for child in el.children:
                    if isinstance(child, Tag):
                        walk(child)

        walk(soup)
        return elements