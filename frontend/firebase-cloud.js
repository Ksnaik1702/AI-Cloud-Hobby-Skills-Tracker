(function () {
  const CDN = 'https://www.gstatic.com/firebasejs/12.19.0/';
  let auth, db, authSdk, store, authReady;
  async function init(config) {
    const modules = await Promise.all([
      import(CDN + 'firebase-app.js'),
      import(CDN + 'firebase-auth.js'),
      import(CDN + 'firebase-firestore.js')
    ]);
    const app = modules[0].initializeApp(config);
    authSdk = modules[1]; store = modules[2];
    auth = authSdk.getAuth(app); db = store.getFirestore(app);
    authReady = new Promise(resolve => authSdk.onAuthStateChanged(auth, resolve));
  }
  async function owned(collectionName, uid) {
    const snap = await store.getDocs(store.query(store.collection(db, collectionName), store.where('userId', '==', uid)));
    return snap.docs.map(d => Object.assign({ id: d.id }, d.data()));
  }
  function active() {
    if (!auth.currentUser) throw new Error('Please sign in to continue.');
    return auth.currentUser;
  }
  async function api(path, options) {
    const method = (options && options.method || 'GET').toUpperCase();
    const body = options && options.body || {};
    const user = auth.currentUser;
    if (path === '/api/auth/register' && method === 'POST') {
      const email = String(body.email || '').trim().toLowerCase();
      const username = String(body.username || '').trim().toLowerCase();
      const name = String(body.name || '').trim();
      if (!/^[a-z0-9_]{3,30}$/.test(username)) throw new Error('Username: 3–30 lowercase letters, numbers, or underscores.');
      const handleRef = store.doc(db, 'handles', username);
      const credential = await authSdk.createUserWithEmailAndPassword(auth, email, String(body.password || ''));
      const profile = { userId: credential.user.uid, email: email, username: username, name: name, bio: '', interests: '', createdAt: new Date().toISOString() };
      try {
        await store.runTransaction(db, async transaction => {
          const latest = await transaction.get(handleRef);
          if (latest.exists()) throw new Error('That username is already in use.');
          transaction.set(handleRef, { userId: credential.user.uid });
          transaction.set(store.doc(db, 'profiles', credential.user.uid), profile);
        });
      } catch (error) {
        await authSdk.deleteUser(credential.user);
        throw error;
      }
      await authSdk.updateProfile(credential.user, { displayName: name });
      return { token: await credential.user.getIdToken(), user: Object.assign({ id: credential.user.uid }, profile) };
    }
    if (path === '/api/auth/login' && method === 'POST') {
      const credential = await authSdk.signInWithEmailAndPassword(auth, String(body.email || '').trim(), String(body.password || ''));
      const profile = await store.getDoc(store.doc(db, 'profiles', credential.user.uid));
      return { token: await credential.user.getIdToken(), user: Object.assign({ id: credential.user.uid }, profile.data()) };
    }
    if (path === '/api/auth/logout') { await authSdk.signOut(auth); return { ok: true }; }
    const current = active();
    const uid = current.uid;
    if (path === '/api/profile' && method === 'GET') {
      const snap = await store.getDoc(store.doc(db, 'profiles', uid));
      return Object.assign({ id: uid, email: current.email || '' }, snap.data());
    }
    if (path === '/api/profile' && method === 'PUT') {
      const ref = store.doc(db, 'profiles', uid);
      const snap = await store.getDoc(ref);
      const profile = Object.assign({}, snap.data(), {
        name: String(body.name || '').trim().slice(0, 80),
        bio: String(body.bio || '').slice(0, 500),
        interests: String(body.interests || '').slice(0, 240)
      });
      await store.setDoc(ref, profile, { merge: true });
      return Object.assign({ id: uid, email: current.email || '' }, profile);
    }
    if (path === '/api/skills' && method === 'GET') {
      const skills = await owned('skills', uid);
      const practice = await owned('practice', uid);
      return skills.map(s => Object.assign({}, s, { practice_minutes: practice.filter(p => p.skillId === s.id).reduce((n, p) => n + Number(p.minutes || 0), 0) }));
    }
    if (path === '/api/skills' && method === 'POST') {
      const ref = store.doc(store.collection(db, 'skills'));
      const value = { userId: uid, name: String(body.name || '').trim(), category: body.category || 'Other', level: body.level || 'BEGINNER', target_level: body.target_level || 'ADVANCED', description: body.description || '', status: 'ACTIVE', createdAt: new Date().toISOString() };
      if (!value.name) throw new Error('Skill name is required.');
      await store.setDoc(ref, value);
      return Object.assign({ id: ref.id }, value);
    }
    const parts = path.split('/').filter(Boolean);
    if (parts[1] === 'skills' && parts.length === 3 && method === 'DELETE') {
      const goals = await owned('goals', uid);
      const sessions = await owned('practice', uid);
      await store.deleteDoc(store.doc(db, 'skills', parts[2]));
      const refs = goals.filter(g => g.skillId === parts[2]).map(g => store.doc(db, 'goals', g.id));
      sessions.filter(p => p.skillId === parts[2]).forEach(p => refs.push(store.doc(db, 'practice', p.id)));
      for (const ref of refs) await store.deleteDoc(ref);
      return { ok: true };
    }
    if (path === '/api/goals' && method === 'GET') {
      const goals = await owned('goals', uid);
      const skills = await owned('skills', uid);
      const sessions = await owned('practice', uid);
      return goals.map(g => {
        const s = skills.find(x => x.id === g.skillId);
        const current = sessions.filter(p => p.skillId === g.skillId).reduce((n, p) => n + Number(p.minutes || 0), 0) / 60;
        return Object.assign({}, g, { skill_name: s ? s.name : 'Skill', current: current, progress: g.target ? Math.min(100, Math.round(current / g.target * 100)) : 0 });
      });
    }
    if (path === '/api/goals' && method === 'POST') {
      const ref = store.doc(store.collection(db, 'goals'));
      const value = { userId: uid, skillId: body.skill_id, title: body.title || 'Practice goal', target: Number(body.target), unit: 'hours', deadline: body.deadline || '', createdAt: new Date().toISOString() };
      if (!value.skillId || value.target <= 0) throw new Error('Choose a skill and enter a target above zero.');
      await store.setDoc(ref, value);
      return { id: ref.id };
    }
    if (path === '/api/practice' && method === 'GET') {
      const sessions = await owned('practice', uid);
      const skills = await owned('skills', uid);
      return sessions.map(p => Object.assign({}, p, { skill_id: p.skillId, skill_name: (skills.find(s => s.id === p.skillId) || {}).name || 'Skill', practiced_at: p.practicedAt })).sort((a, b) => new Date(b.practiced_at) - new Date(a.practiced_at)).slice(0, 30);
    }
    if (path === '/api/practice' && method === 'POST') {
      const ref = store.doc(store.collection(db, 'practice'));
      const value = { userId: uid, skillId: body.skill_id, minutes: Number(body.minutes), activity: body.activity || 'Practice session', notes: body.notes || '', practicedAt: body.practiced_at || new Date().toISOString() };
      if (!value.skillId || !Number.isInteger(value.minutes) || value.minutes < 1 || value.minutes > 1440) throw new Error('Choose a skill and enter 1 to 1,440 minutes.');
      await store.setDoc(ref, value);
      return { id: ref.id };
    }
    if (path === '/api/analytics/dashboard' && method === 'GET') {
      const skills = await owned('skills', uid);
      const sessions = await owned('practice', uid);
      const goals = await owned('goals', uid);
      const total = sessions.reduce((n, p) => n + Number(p.minutes || 0), 0);
      const dates = new Set(sessions.map(p => String(p.practicedAt || '').slice(0, 10)));
      let cursor = new Date(); cursor.setUTCHours(0, 0, 0, 0);
      if (!dates.has(cursor.toISOString().slice(0, 10))) cursor.setUTCDate(cursor.getUTCDate() - 1);
      let streak = 0;
      while (dates.has(cursor.toISOString().slice(0, 10))) { streak++; cursor.setUTCDate(cursor.getUTCDate() - 1); }
      const skillMinutes = skills.map(s => Object.assign({}, s, { minutes: sessions.filter(p => p.skillId === s.id).reduce((n,p) => n + Number(p.minutes || 0), 0) }));
      const recent = sessions.map(p => Object.assign({}, p, { skill_name: (skills.find(s => s.id === p.skillId) || {}).name || 'Skill', practiced_at: p.practicedAt })).sort((a,b) => new Date(b.practiced_at)-new Date(a.practiced_at));
      const weekStart = new Date();
      weekStart.setUTCHours(0, 0, 0, 0);
      weekStart.setUTCDate(weekStart.getUTCDate() - 6);
      const weekBuckets = Object.create(null);
      sessions.forEach(session => {
        const when = session.practicedAt || '';
        if (new Date(when) >= weekStart) {
          const day = new Date(when).toISOString().slice(0, 10);
          weekBuckets[day] = (weekBuckets[day] || 0) + Number(session.minutes || 0);
        }
      });
      const weekly = Object.keys(weekBuckets).map(day => ({ day: day, minutes: weekBuckets[day] })).sort((a,b)=>a.day.localeCompare(b.day));
      const completed = goals.filter(g => sessions.filter(p => p.skillId === g.skillId).reduce((n,p)=>n+Number(p.minutes||0),0)/60 >= g.target).length;
      return { total_minutes: total, total_hours: Math.round(total/6)/10, active_skills: skills.filter(s=>s.status==='ACTIVE').length, skills: skillMinutes, weekly: weekly, streak: streak, goals_total: goals.length, goals_completed: completed, recent: recent.slice(0,5) };
    }
    if (path === '/api/feed' && method === 'GET') {
      const snap = await store.getDocs(store.query(store.collection(db, 'posts'), store.orderBy('createdAt', 'desc'), store.limit(30)));
      const posts = [];
      for (const item of snap.docs) {
        const d = item.data();
        const likes = await store.getDocs(store.collection(db, 'posts', item.id, 'likes'));
        const comments = await store.getDocs(store.collection(db, 'posts', item.id, 'comments'));
        const myLike = await store.getDoc(store.doc(db, 'posts', item.id, 'likes', uid));
        posts.push({ id: item.id, user_id: d.userId, name: d.name, username: d.username, content: d.content, skill_name: d.skill_name || '', media_name: d.mediaUrl || null, created_at: d.createdAt, likes: likes.size, comments: comments.size, liked: myLike.exists() });
      }
      return posts.sort((a,b)=>new Date(b.created_at)-new Date(a.created_at));
    }
    if (path === '/api/posts' && method === 'POST') {
      const content = String(body.content || '').trim();
      if (!content || content.length > 1000) throw new Error('Write a post up to 1,000 characters.');
      const profile = await store.getDoc(store.doc(db, 'profiles', uid));
      const p = profile.data() || {};
      const ref = store.doc(store.collection(db, 'posts'));
      await store.setDoc(ref, { userId: uid, name: p.name || current.displayName || 'Hobbyloop member', username: p.username || 'member', content: content, mediaUrl: body.media_url || null, mediaPath: body.media_path || null, skill_name: '', createdAt: new Date().toISOString() });
      return { id: ref.id };
    }
    if (parts[1] === 'posts' && parts.length === 4 && parts[3] === 'like') {
      const ref = store.doc(db, 'posts', parts[2], 'likes', uid);
      if (method === 'POST') await store.setDoc(ref, { userId: uid, createdAt: new Date().toISOString() });
      else if (method === 'DELETE') await store.deleteDoc(ref);
      return { ok: true };
    }
    if (parts[1] === 'posts' && parts.length === 4 && parts[3] === 'comments') {
      const ref = store.collection(db, 'posts', parts[2], 'comments');
      if (method === 'GET') {
        const snap = await store.getDocs(ref);
        return snap.docs.map(d => Object.assign({ id: d.id }, d.data())).sort((a,b)=>(a.createdAt||'').localeCompare(b.createdAt||''));
      }
      if (method === 'POST') {
        const text = String(body.text || '').trim();
        if (!text || text.length > 500) throw new Error('Write a comment up to 500 characters.');
        const profile = await store.getDoc(store.doc(db, 'profiles', uid));
        const p = profile.data() || {};
        const comment = store.doc(ref);
        await store.setDoc(comment, { userId: uid, name: p.name || 'Hobbyloop member', username: p.username || 'member', text: text, createdAt: new Date().toISOString() });
        return { id: comment.id };
      }
    }
    if (parts[1] === 'posts' && parts.length === 3 && method === 'DELETE') {
      const ref = store.doc(db, 'posts', parts[2]);
      const post = await store.getDoc(ref);
      if (!post.exists() || post.data().userId !== uid) return { ok: false };
      if (post.data().mediaPath && String(post.data().mediaPath).startsWith('community/' + uid + '/')) {
      }
      const likes = await store.getDocs(store.collection(db, 'posts', parts[2], 'likes'));
      const comments = await store.getDocs(store.collection(db, 'posts', parts[2], 'comments'));
      const refs = likes.docs.map(d => d.ref).concat(comments.docs.map(d => d.ref), [ref]);
      for (const item of refs) await store.deleteDoc(item);
      return { ok: true };
    }
    throw new Error('Cloud route not connected: ' + path);
  }

  window.HobbyloopFirebase = {
    init: init,
    readyUser: async function () { return authReady ? await authReady : null; },
    signOut: async function () { if (auth) await authSdk.signOut(auth); },
    api: api
  };
})();





