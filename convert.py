import html
import json
from datetime import datetime
from pathlib import Path

from format import formator


class convertor:
    def __init__(self,baseurl_bool=True,format=formator()):
        self.format = format
        self.base_dict = dict()
        self.base_dict.update(self.format.base)
        self.baseurl_str = self.base_dict["base_url"] if baseurl_bool else str()
    #
    def template(self,input_str:str,input_dict:dict) -> str:
        return self.format.structure[input_str].format(**input_dict)
    #
    def post(self):
        posts_list = list()
        posts_dict = dict()
        categories_dict = dict()
        post_member_list = list()
        post_atom_list = list()
        for post_path in sorted(list(Path("post_files").glob('*.*'))):
            name_list = post_path.name.split(".")
            extention_str = name_list[-1]
            if len(name_list) > 1 and extention_str in ["md","html"]:
                content_dict = self.format.parse(open(post_path).read())
                header_dict = dict()
                header_dict.update(content_dict["header"])
                canonical_str = header_dict["short"][0]
                date_obj = datetime.fromisoformat(header_dict["date"])
                datetime_str = date_obj.strftime("%Y/%m/%d")
                #
                category_parent_dict = dict()
                category_content_list = list()
                for category_str in header_dict["categories"]:
                    category_child_dict = {
                        "title" : "·".join([category_str,self.base_dict["base_title"]]),
                        "category_title" : category_str,
                        "category_url" : F"{self.baseurl_str}/category/{category_str}/",
                    }
                    category_parent_dict[category_str] = category_child_dict
                    category_content_list.append(self.template("format_categories_in_post",category_child_dict))
                    #
                    category_detail_dict = categories_dict.get(category_str,dict())
                    category_detail_dict.update(category_child_dict)
                    categories_dict[category_str] = category_detail_dict
                #
                categories_str = "/".join(header_dict["categories"])
                url_list = [F"{self.baseurl_str}/{categories_str}/{datetime_str}/{n}/" for n in header_dict["short"]] # type: ignore
                url_list.extend([F"{self.baseurl_str}/{categories_str}/{n}/" for n in header_dict["short"]]) # type: ignore
                url_list.extend([F"{self.baseurl_str}/{datetime_str}/{n}/" for n in header_dict["short"]]) # type: ignore
                url_list.extend([F"{self.baseurl_str}/{n}/" for n in header_dict["short"]]) # type: ignore
                url_list.append(F"{self.baseurl_str}/post/{canonical_str}/")
                content_str = content_dict["content"]
                preview_str = content_str.split(self.base_dict["separator_preview"])[0]
                escaped_str = html.escape(preview_str)
                post_dict = {
                    "title" : " · ".join([header_dict["title"],self.base_dict["base_title"]]),
                    "short_list" : header_dict["short"],
                    "short_canonical" : canonical_str,
                    "categories_dict" : category_parent_dict,
                    "date_iso" : header_dict["date"],
                    "date_show" : date_obj.strftime("%a, %b %-d, %Y"),
                    "date_822" : date_obj.strftime("%a, %d %b %Y %T %z"),
                    "date_8601" : date_obj.isoformat(),
                    "post_title" : header_dict["title"],
                    "post_urls" : url_list,
                    "post_url" : F"{self.baseurl_str}/{datetime_str}/{canonical_str}/",
                    "post_categories": "".join(category_content_list),
                    "content_full" : content_str,
                    "content_preview" : preview_str,
                    "content_escaped" : escaped_str,
                }
                if canonical_str in posts_dict.keys():
                    print(F"ERROR: duplicate canonical_str [{canonical_str}]")  # type: ignore
                else:
                    for category_str in post_dict["categories_dict"].keys():
                        category_detail_dict = categories_dict.get(category_str,dict())
                        category_member_dict = category_detail_dict.get("member",dict())
                        title_str = post_dict["post_title"]
                        title_short_str = title_str[:15]+"..." if len(title_str) > 18 else title_str
                        category_member_dict[canonical_str] = {
                            "member_title" : title_str,
                            "member_short" : title_short_str,
                            "member_url" : post_dict["post_url"],
                            "member_date" : post_dict["date_show"],
                        }
                        category_detail_dict["member"] = category_member_dict
                        categories_dict[category_str] = category_detail_dict
                    posts_list.append(post_dict)
                    posts_dict[canonical_str] = len(posts_list)-1
        #
        categories_content_list = list()
        for category_str in categories_dict.keys():
            category_detail_dict = categories_dict[category_str]
            content_list = list()
            section_list = list()
            for member_dict in category_detail_dict["member"].values():
                content_list.append(self.template("format_member_in_category_content",member_dict))
                section_list.append(self.template("format_member_in_category_section",member_dict))
            category_detail_dict["category_content"] = "".join(content_list)
            category_detail_dict["category_section"] = "".join(section_list)
            categories_dict[category_str] = category_detail_dict
            categories_content_list.append(self.template("format_categories_by_section",category_detail_dict))
        self.base_dict["categories_content_list"] = "".join(categories_content_list)
        #
        for post_pos, post_dict in enumerate(posts_list):
            canonical_str = post_dict["short_canonical"]
            releted_dict = dict()
            for category_str in post_dict["categories_dict"].keys():
                category_member_dict = categories_dict[category_str]["member"]
                releted_dict.update({x:self.template("format_related_member",y) for x,y in category_member_dict.items()})
            related_order_dict = {posts_dict[n]:n for n in releted_dict.keys() if n != canonical_str}
            related_order_list = [releted_dict[related_order_dict[n]] for n in sorted(list(related_order_dict.keys()),reverse=True)]
            related_list = related_order_list[:3] if len(related_order_list) > 3 else related_order_list
            related_str = "".join(related_list)
            # post_dict["related_order_list"] = related_order_list
            post_dict["related_content"] = self.template("format_related_frame",{"related_posts_list":related_str})
            posts_list[post_pos] = post_dict
        #
        reversed_posts_dict = {y:x for x,y in posts_dict.items()}
        reversed_order_list = [posts_list[post_pos] for post_pos in sorted(reversed_posts_dict.keys(),reverse=True)]
        for post_dict in reversed_order_list:
            if post_dict["content_full"] == post_dict["content_preview"]:
                post_member_list.append(self.template("format_post_container_full",post_dict))
            else:
                post_member_list.append(self.template("format_post_container_preview",post_dict))
            atom_dict = dict()
            atom_dict.update(post_dict)
            atom_bool = self.base_dict["base_url"] in post_dict["post_url"]
            atom_dict["base_url"] = str() if atom_bool else self.base_dict["base_url"]
            post_atom_list.append(self.template("format_atom_post",atom_dict))
        self.base_dict["post_member_list"] = post_member_list
        self.base_dict["post_content_list"] = "".join(post_member_list)
        self.base_dict["post_atom_list"] = post_atom_list
        self.base_dict["atom_content_list"] = "".join(post_atom_list)
        #
        #
        Path("mid_files").mkdir(exist_ok=True)
        with open("mid_files/post.json","w") as t:
            json.dump(posts_list,t,indent=0)
        with open("mid_files/post_pos.json","w") as t:
            json.dump(posts_dict,t,indent=0)
        with open("mid_files/categories.json","w") as t:
            json.dump(categories_dict,t,indent=0)
        with open("mid_files/base.json","w") as t:
            json.dump(self.base_dict,t,indent=0)
    #
    def page(self):
        pages_dict = dict()
        for page_path in sorted(list(Path("page_files").glob('*.*'))):
            name_list = page_path.name.split(".")
            extention_str = name_list[-1]
            content_dict = self.format.parse(open(page_path).read())
            header_dict = dict()
            header_dict.update(content_dict["header"])
            canonical_str = header_dict["title"]
            url_list = [F"{self.baseurl_str}{n}" for n in header_dict["path"]]
            url_str = url_list[0]
            if "skip" not in header_dict.keys():
                url_list.append(F"{self.baseurl_str}/pages{url_str}")
            page_dict = {
                "title" : " · ".join([canonical_str,self.base_dict["base_title"]]),
                "page_title" : canonical_str,
                "page_urls" : url_list,
                "page_url" : url_str,
            }
            if "skip" not in header_dict.keys():
                if "content" in content_dict.keys():
                    page_dict["page_content"] = content_dict["content"]
                elif header_dict["frame"] in content_dict["frame"].keys():
                    page_dict["page_content"] = content_dict["frame"][header_dict["frame"]]
                else:
                    print(F"ERROR: can get content from {canonical_str}")
            if "layout" in header_dict.keys() and header_dict["frame"] in content_dict["frame"].keys():
                page_dict["layout_content"] = content_dict["frame"][header_dict["frame"]]
            if "base" in header_dict.keys():
                page_dict["base"] = header_dict["base"]
            if "more" in header_dict.keys():
                page_dict["more"] = header_dict["more"]
            if canonical_str in pages_dict.keys():
                print(F"ERROR: duplicate canonical_str [{canonical_str}]")
            else:
                pages_dict[canonical_str] = page_dict
        page_content_list = list()
        for page_str in pages_dict.keys():
            page_detail_dict = pages_dict[page_str]
            page_content_list.append(self.template("format_pages_in_sidebar",page_detail_dict))
        self.base_dict["page_content_list"] = "".join(page_content_list)
        #
        Path("mid_files").mkdir(exist_ok=True)
        with open("mid_files/page.json","w") as t:
            json.dump(pages_dict,t,indent=0)
        with open("mid_files/base.json","w") as t:
            json.dump(self.base_dict,t,indent=0)