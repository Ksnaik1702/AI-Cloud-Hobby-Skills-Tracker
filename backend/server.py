"""Hobbyloop local REST API. Standard-library only for an easy student setup."""
from __future__ import annotations
import base64, hashlib, hmac, json, mimetypes, os, secrets, sqlite3, time
from datetime import date, datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(__file__).resolve().parent / "data"
UPLOADS = Path(__file__).resolve().parent / "uploads"
DB = DATA / "hobbyloop.db"
DATA.mkdir(exist_ok=True); UPLOADS.mkdir(exist_ok=True)
SECRET = os.getenv("HOBBYLOOP_SECRET", "local-demo-only-change-before-deploy").encode()

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, username TEXT UNIQUE NOT NULL, name TEXT NOT NULL, password_hash TEXT NOT NULL, bio TEXT DEFAULT '', interests TEXT DEFAULT '', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS skills(id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, name TEXT NOT NULL, category TEXT NOT NULL, level TEXT NOT NULL, target_level TEXT NOT NULL, description TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'ACTIVE', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS goals(id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, skill_id TEXT NOT NULL REFERENCES skills(id) ON DELETE CASCADE, title TEXT NOT NULL, target REAL NOT NULL, unit TEXT NOT NULL, deadline TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS practice(id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, skill_id TEXT NOT NULL REFERENCES skills(id) ON DELETE CASCADE, minutes INTEGER NOT NULL, activity TEXT NOT NULL, notes TEXT DEFAULT '', practiced_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS posts(id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, skill_id TEXT REFERENCES skills(id) ON DELETE SET NULL, content TEXT NOT NULL, media_name TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS likes(post_id TEXT NOT NULL REFERENCES posts(id) ON DELETE CASCADE, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, created_at TEXT NOT NULL, PRIMARY KEY(post_id,user_id));
CREATE TABLE IF NOT EXISTS comments(id TEXT PRIMARY KEY, post_id TEXT NOT NULL REFERENCES posts(id) ON DELETE CASCADE, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, text TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_practice_user_date ON practice(user_id, practiced_at);
CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at DESC);
"""

def connect():
    db=sqlite3.connect(DB); db.row_factory=sqlite3.Row; db.execute("PRAGMA foreign_keys=ON"); return db
def now(): return datetime.now(timezone.utc).isoformat()
def uid(): return secrets.token_urlsafe(12)
def row(r): return dict(r) if r else None
def progress_percent(current, target):
    return min(100, max(0, round(float(current) / float(target) * 100))) if float(target) > 0 else 0
def pw_hash(password, salt=None):
    salt=salt or secrets.token_bytes(16)
    return base64.b64encode(salt+hashlib.pbkdf2_hmac('sha256',password.encode(),salt,240000)).decode()
def pw_ok(password, encoded):
    data=base64.b64decode(encoded); return hmac.compare_digest(data[16:],hashlib.pbkdf2_hmac('sha256',password.encode(),data[:16],240000))
def token(user_id):
    body=base64.urlsafe_b64encode(json.dumps({'sub':user_id,'exp':int(time.time())+86400}).encode()).decode().rstrip('=')
    sig=base64.urlsafe_b64encode(hmac.new(SECRET,body.encode(),hashlib.sha256).digest()).decode().rstrip('=')
    return body+'.'+sig
def token_user(value):
    try:
        body,sig=value.split('.',1); expected=base64.urlsafe_b64encode(hmac.new(SECRET,body.encode(),hashlib.sha256).digest()).decode().rstrip('=')
        if not hmac.compare_digest(sig,expected): return None
        claims=json.loads(base64.urlsafe_b64decode(body+'='*(-len(body)%4)))
        return claims['sub'] if claims['exp']>time.time() else None
    except Exception: return None

def init():
    with connect() as db:
        db.executescript(SCHEMA)
        if db.execute('SELECT COUNT(*) FROM posts').fetchone()[0]==0:
            samples=[('Maya Chen','mayamakes','Painting','A tiny reminder that progress is still progress. Finished the first color study for my weekend series. 🎨'),('Arjun Rao','arjun.codes','Coding','Built my first little weather dashboard this week. The best part was finally understanding async requests.'),('Sam Rivera','sam.moves','Fitness','Back to a steady routine: three short sessions this week, and it feels good to show up.')]
            for name,handle,skill,content in samples:
                user=db.execute('SELECT id FROM users WHERE username=?',(handle,)).fetchone()
                if not user:
                    u=uid(); db.execute('INSERT INTO users VALUES(?,?,?,?,?,?,?,?)',(u,handle+'@demo.hobbyloop',handle,name,pw_hash(secrets.token_urlsafe()),'',skill,now())); user={'id':u}
                sk=db.execute('SELECT id FROM skills WHERE user_id=? AND name=?',(user['id'],skill)).fetchone()
                if not sk:
                    sid=uid(); db.execute('INSERT INTO skills VALUES(?,?,?,?,?,?,?,?,?)',(sid,user['id'],skill,skill,'BEGINNER','ADVANCED','Synthetic community demo profile','ACTIVE',now())); sk={'id':sid}
                db.execute('INSERT INTO posts VALUES(?,?,?,?,?,?)',(uid(),user['id'],sk['id'],content,None,now()))

class Handler(BaseHTTPRequestHandler):
    server_version='Hobbyloop/0.1'
    def log_message(self, fmt,*args): print(f"{self.address_string()} {fmt%args}")
    def send(self,status,data=None,content_type='application/json; charset=utf-8'):
        raw=(json.dumps(data,ensure_ascii=False).encode() if content_type.startswith('application/json') else data)
        self.send_response(status); self.send_header('Content-Type',content_type); self.send_header('Content-Length',str(len(raw))); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Headers','Content-Type, Authorization'); self.send_header('Access-Control-Allow-Methods','GET, POST, PUT, DELETE, OPTIONS'); self.end_headers(); self.wfile.write(raw)
    def body(self):
        n=int(self.headers.get('Content-Length','0'))
        if n>6_000_000: raise ValueError('Request is too large')
        return json.loads(self.rfile.read(n) or b'{}')
    def auth(self,required=True):
        h=self.headers.get('Authorization',''); user=token_user(h.removeprefix('Bearer ')) if h.startswith('Bearer ') else None
        if required and not user: raise PermissionError('Please sign in to continue')
        return user
    def json_error(self,status,msg): self.send(status,{'error':msg})
    def do_OPTIONS(self): self.send(204,b'', 'text/plain')
    def do_GET(self): self.route('GET')
    def do_POST(self): self.route('POST')
    def do_PUT(self): self.route('PUT')
    def do_DELETE(self): self.route('DELETE')
    def route(self,method):
      try:
        path=urlparse(self.path).path; bits=[b for b in path.split('/') if b]; data=self.body() if method in ('POST','PUT') and not path.startswith('/api/files/') else {}; user=self.auth(path.startswith('/api') and path not in ('/api/feed','/api/health','/api/auth/register','/api/auth/login'))
        with connect() as db:
          if path=='/' or path=='/index.html':
            f=(ROOT/'frontend'/'index.html').read_bytes(); return self.send(200,f,'text/html; charset=utf-8')
          if path.startswith('/frontend/') or path in {'/app.js','/styles.css','/firebase-config.js','/firebase-cloud.js'}:
            asset=Path(path).name
            if asset not in {'app.js','styles.css','firebase-config.js','firebase-cloud.js'}: return self.json_error(404,'Asset not found.')
            f=(ROOT/'frontend'/asset).read_bytes(); return self.send(200,f,mimetypes.guess_type(path)[0] or 'application/octet-stream')
          if path.startswith('/uploads/'):
            name=Path(path).name; f=(UPLOADS/name).read_bytes(); return self.send(200,f,mimetypes.guess_type(name)[0] or 'application/octet-stream')
          if path=='/api/auth/register' and method=='POST':
            email=str(data.get('email','')).strip().lower(); name=str(data.get('name','')).strip(); username=str(data.get('username','')).strip().lower(); password=str(data.get('password',''))
            if not name or not email or '@' not in email or len(username)<3 or len(password)<8: return self.json_error(400,'Enter a name, valid email, username (3+ characters), and password (8+ characters).')
            user_id=uid(); db.execute('INSERT INTO users VALUES(?,?,?,?,?,?,?,?)',(user_id,email,username,name,pw_hash(password),'','',now())); return self.send(201,{'token':token(user_id),'user':row(db.execute('SELECT id,email,username,name,bio,interests,created_at FROM users WHERE id=?',(user_id,)).fetchone())})
          if path=='/api/auth/login' and method=='POST':
            r=db.execute('SELECT * FROM users WHERE email=?',(str(data.get('email','')).lower(),)).fetchone()
            if not r or not pw_ok(str(data.get('password','')),r['password_hash']): return self.json_error(401,'Email or password is incorrect.')
            return self.send(200,{'token':token(r['id']),'user':row(db.execute('SELECT id,email,username,name,bio,interests,created_at FROM users WHERE id=?',(r['id'],)).fetchone())})
          if path=='/api/auth/logout' and method=='POST': return self.send(200,{'ok':True})
          if path=='/api/profile' and method=='GET': return self.send(200,row(db.execute('SELECT id,email,username,name,bio,interests,created_at FROM users WHERE id=?',(user,)).fetchone()))
          if path=='/api/profile' and method=='PUT':
            db.execute('UPDATE users SET name=?,bio=?,interests=? WHERE id=?',(str(data.get('name','')).strip()[:80],str(data.get('bio',''))[:500],str(data.get('interests',''))[:240],user)); return self.send(200,row(db.execute('SELECT id,email,username,name,bio,interests,created_at FROM users WHERE id=?',(user,)).fetchone()))
          if path=='/api/skills' and method=='GET': return self.send(200,[dict(r)|{'practice_minutes':r['practice_minutes'] or 0} for r in db.execute('SELECT s.*,SUM(p.minutes) practice_minutes FROM skills s LEFT JOIN practice p ON p.skill_id=s.id WHERE s.user_id=? GROUP BY s.id ORDER BY s.created_at DESC',(user,))])
          if path=='/api/skills' and method=='POST':
            sid=uid(); name=str(data.get('name','')).strip();
            if not name: return self.json_error(400,'Skill name is required.')
            db.execute('INSERT INTO skills VALUES(?,?,?,?,?,?,?,?,?)',(sid,user,name[:80],str(data.get('category','Other'))[:40],data.get('level','BEGINNER'),data.get('target_level','ADVANCED'),str(data.get('description',''))[:500],'ACTIVE',now())); return self.send(201,row(db.execute('SELECT * FROM skills WHERE id=?',(sid,)).fetchone()))
          if len(bits)==3 and bits[:2]==['api','skills'] and method=='DELETE':
            cur=db.execute('DELETE FROM skills WHERE id=? AND user_id=?',(bits[2],user)); return self.send(200,{'ok':bool(cur.rowcount)})
          if path=='/api/goals' and method=='GET':
            return self.send(200,[dict(r)|{'current':r['current'] or 0,'progress':progress_percent(r['current'] or 0, r['target'])} for r in db.execute('SELECT g.*,s.name skill_name,(SELECT SUM(minutes)/60.0 FROM practice p WHERE p.skill_id=g.skill_id AND p.user_id=g.user_id) current FROM goals g JOIN skills s ON s.id=g.skill_id WHERE g.user_id=? ORDER BY g.created_at DESC',(user,))])
          if path=='/api/goals' and method=='POST':
            gid=uid(); target=float(data.get('target',0)); sk=db.execute('SELECT id FROM skills WHERE id=? AND user_id=?',(data.get('skill_id'),user)).fetchone()
            if not sk or target<=0: return self.json_error(400,'Choose one of your skills and enter a target above zero.')
            db.execute('INSERT INTO goals VALUES(?,?,?,?,?,?,?,?)',(gid,user,data.get('skill_id'),str(data.get('title','Practice goal'))[:120],target,str(data.get('unit','hours'))[:24],data.get('deadline'),now())); return self.send(201,{'id':gid})
          if path=='/api/practice' and method=='GET':
            return self.send(200,[dict(r) for r in db.execute('SELECT p.*,s.name skill_name FROM practice p JOIN skills s ON s.id=p.skill_id WHERE p.user_id=? ORDER BY practiced_at DESC LIMIT 30',(user,))])
          if path=='/api/practice' and method=='POST':
            minutes=int(data.get('minutes',0)); sk=db.execute('SELECT id FROM skills WHERE id=? AND user_id=?',(data.get('skill_id'),user)).fetchone()
            if not sk or minutes<1 or minutes>1440: return self.json_error(400,'Choose a skill and enter 1 to 1,440 practice minutes.')
            pid=uid(); db.execute('INSERT INTO practice VALUES(?,?,?,?,?,?,?)',(pid,user,data['skill_id'],minutes,str(data.get('activity','Practice session'))[:120],str(data.get('notes',''))[:500],data.get('practiced_at') or now())); return self.send(201,{'id':pid})
          if path=='/api/analytics/dashboard' and method=='GET': return self.send(200,self.analytics(db,user))
          if path=='/api/feed' and method=='GET':
            q=parse_qs(urlparse(self.path).query); limit=min(30,max(1,int(q.get('limit',['20'])[0]))); offset=max(0,int(q.get('offset',['0'])[0]))
            posts=[]
            for r in db.execute('SELECT p.*,u.name,u.username,s.name skill_name,(SELECT COUNT(*) FROM likes l WHERE l.post_id=p.id) likes,(SELECT COUNT(*) FROM comments c WHERE c.post_id=p.id) comments,EXISTS(SELECT 1 FROM likes l WHERE l.post_id=p.id AND l.user_id=?) liked FROM posts p JOIN users u ON u.id=p.user_id LEFT JOIN skills s ON s.id=p.skill_id ORDER BY p.created_at DESC LIMIT ? OFFSET ?',(user,limit,offset)):
              posts.append(dict(r))
            return self.send(200,posts)
          if path=='/api/posts' and method=='POST':
            content=str(data.get('content','')).strip()
            if not content or len(content)>1000: return self.json_error(400,'Write a post (up to 1,000 characters).')
            skill=db.execute('SELECT id FROM skills WHERE id=? AND user_id=?',(data.get('skill_id'),user)).fetchone() if data.get('skill_id') else None
            media=data.get('media_url'); media=Path(str(media)).name if isinstance(media,str) and str(media).startswith('/uploads/') else None
            pid=uid(); db.execute('INSERT INTO posts VALUES(?,?,?,?,?,?)',(pid,user,skill['id'] if skill else None,content,('/uploads/'+media) if media else None,now())); return self.send(201,{'id':pid})
          if len(bits)==4 and bits[:2]==['api','posts'] and bits[3]=='like' and method=='POST':
            db.execute('INSERT OR IGNORE INTO likes VALUES(?,?,?)',(bits[2],user,now())); return self.send(200,{'ok':True})
          if len(bits)==4 and bits[:2]==['api','posts'] and bits[3]=='like' and method=='DELETE':
            db.execute('DELETE FROM likes WHERE post_id=? AND user_id=?',(bits[2],user)); return self.send(200,{'ok':True})
          if len(bits)==4 and bits[:2]==['api','posts'] and bits[3]=='comments' and method=='GET':
            return self.send(200,[dict(r) for r in db.execute('SELECT c.*,u.name,u.username FROM comments c JOIN users u ON u.id=c.user_id WHERE post_id=? ORDER BY created_at',(bits[2],))])
          if len(bits)==4 and bits[:2]==['api','posts'] and bits[3]=='comments' and method=='POST':
            text=str(data.get('text','')).strip()
            if not text or len(text)>500: return self.json_error(400,'Write a comment (up to 500 characters).')
            cid=uid(); db.execute('INSERT INTO comments VALUES(?,?,?,?,?)',(cid,bits[2],user,text,now())); return self.send(201,{'id':cid})
          if len(bits)==3 and bits[:2]==['api','posts'] and method=='DELETE':
            cur=db.execute('DELETE FROM posts WHERE id=? AND user_id=?',(bits[2],user)); return self.send(200,{'ok':bool(cur.rowcount)})
          if path=='/api/files/upload' and method=='POST': return self.upload(user)
          if path=='/api/health': return self.send(200,{'status':'ok','mode':'local'})
          if path.startswith('/api/'): return self.json_error(404,'That API route was not found.')
          return self.json_error(404,'Page not found.')
      except PermissionError as e: self.json_error(401,str(e))
      except sqlite3.IntegrityError: self.json_error(409,'That email or username is already in use.')
      except (ValueError,TypeError,KeyError) as e: self.json_error(400,str(e) or 'Invalid request.')
      except FileNotFoundError: self.json_error(404,'File not found.')
      except Exception as e: print('API error:',repr(e)); self.json_error(500,'Something went wrong. Please try again.')
    def upload(self,user):
      length=int(self.headers.get('Content-Length','0'))
      if length>5_000_000: return self.json_error(413,'File must be smaller than 5 MB.')
      kind=self.headers.get('Content-Type',''); boundary=kind.split('boundary=')[-1].encode(); raw=self.rfile.read(length)
      parts=raw.split(b'--'+boundary)
      part=next((p for p in parts if b'filename=' in p),None)
      if not part: return self.json_error(400,'Choose an image to upload.')
      head,payload=part.split(b'\r\n\r\n',1); payload=payload.rsplit(b'\r\n',1)[0]
      filename=head.decode('latin1').split('filename="')[-1].split('"')[0]; ext=Path(filename).suffix.lower()
      allowed={'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'}
      if ext not in allowed or len(payload)>4_500_000: return self.json_error(400,'Upload a PNG, JPG, or WebP image under 4.5 MB.')
      stored=uid()+ext; (UPLOADS/stored).write_bytes(payload); return self.send(201,{'url':'/uploads/'+stored,'name':Path(filename).name})
    def analytics(self,db,user):
      total=db.execute('SELECT COALESCE(SUM(minutes),0) FROM practice WHERE user_id=?',(user,)).fetchone()[0]
      skills=[dict(r) for r in db.execute('SELECT s.id,s.name,s.category,s.level,s.status,COALESCE(SUM(p.minutes),0) minutes FROM skills s LEFT JOIN practice p ON p.skill_id=s.id WHERE s.user_id=? GROUP BY s.id ORDER BY minutes DESC',(user,))]
      days={r['day'] for r in db.execute("SELECT DISTINCT date(practiced_at) day FROM practice WHERE user_id=?",(user,))}
      streak=0; cursor=date.today()
      if cursor.isoformat() not in days: cursor-=timedelta(days=1)
      while cursor.isoformat() in days: streak+=1; cursor-=timedelta(days=1)
      since=(datetime.now(timezone.utc)-timedelta(days=6)).isoformat()
      weekly=[dict(r) for r in db.execute("SELECT date(practiced_at) day,SUM(minutes) minutes FROM practice WHERE user_id=? AND practiced_at>=? GROUP BY day ORDER BY day",(user,since))]
      goals=db.execute('SELECT COUNT(*) n FROM goals WHERE user_id=?',(user,)).fetchone()['n']
      completed=sum(1 for g in db.execute('SELECT target,(SELECT COALESCE(SUM(minutes)/60.0,0) FROM practice p WHERE p.user_id=goals.user_id AND p.skill_id=goals.skill_id) current FROM goals WHERE user_id=?',(user,)) if g['current']>=g['target'])
      return {'total_minutes':total,'total_hours':round(total/60,1),'active_skills':sum(1 for s in skills if s['status']=='ACTIVE'),'skills':skills,'weekly':weekly,'streak':streak,'goals_total':goals,'goals_completed':completed,'recent': [dict(r) for r in db.execute('SELECT p.*,s.name skill_name FROM practice p JOIN skills s ON s.id=p.skill_id WHERE p.user_id=? ORDER BY practiced_at DESC LIMIT 5',(user,))]}

if __name__=='__main__':
    init(); host=os.getenv('HOBBYLOOP_HOST','127.0.0.1'); port=int(os.getenv('HOBBYLOOP_PORT','8000'))
    print(f'Hobbyloop is running at http://{host}:{port}')
    ThreadingHTTPServer((host,port),Handler).serve_forever()

