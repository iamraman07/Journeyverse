
from app import app, db, MyCollab, MyCollabLike, MyCollabComment

def sync_counts():
    with app.app_context():
        print("Starting sync of MyCollab counts...")
        collabs = MyCollab.query.all()
        for collab in collabs:
            real_likes = MyCollabLike.query.filter_by(my_collab_id=collab.id).count()
            real_comments = MyCollabComment.query.filter_by(my_collab_id=collab.id).count()
            
            print(f"Project '{collab.project_name}':")
            print(f"  - Stored Likes: {collab.likes}, Real Likes: {real_likes}")
            print(f"  - Stored Comments: {collab.comments}, Real Comments: {real_comments}")
            
            if collab.likes != real_likes or collab.comments != real_comments:
                collab.likes = real_likes
                collab.comments = real_comments
                print("  -> UPDATED")
            else:
                print("  -> OK")
        
        db.session.commit()
        print("Sync complete!")

if __name__ == "__main__":
    sync_counts()
