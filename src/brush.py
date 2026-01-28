import time
from model.action_service import ActionService
from model.auth_service import AuthService
from model.account import PHONE, PASSWORD

actions = ActionService()
cate_list = ["706", "707", "708", "702", "701"]


def main(cate_id):
    # Use ActionService since it has the business logic we need.

    # Check if we need to login
    if not actions.token:
        print("[*] No valid session, initiating login...")
        auth = AuthService()
        if auth.login(PHONE, PASSWORD):
            # Reload session in actions client
            actions.load_session()
        else:
            return

    # 请求10次列表，返回的数据放到一个列表中
    all_posts = []
    for i in range(2):
        if i == 0:
            posts = actions.list_posts(category_id=cate_id)
            all_posts.extend(posts)
        else:
            posts = actions.list_posts(category_id=cate_id, is_top=False)
            all_posts.extend(posts)

    # print(len(all_posts))
    for post in all_posts:
        if not post['isLike']:
            actions.like_post(post['id'], post['categoryId'])
            time.sleep(1)
        if not post['isCollection']:
            actions.collect_post(post['id'], post['categoryId'])
            time.sleep(1)
        # if post['commentNum'] == 0 or not post['isTopping']:
        #     actions.comment_post(post['id'])
        #     time.sleep(1)


if __name__ == "__main__":
    for cate_id in cate_list:
        main(cate_id)
    # actions.comment_post('3958505124310025164')
