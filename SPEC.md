# LEA

## What is LEA
LEA stands for Listening Experience Album — you buy a digital album that exists within its own programming, native to desktop and mobile, ideally receiving the highest quality format from the player. The album also includes liner notes, narrations from the artist, artwork, and whatever exclusive treats the artist decides to include.

## The problem
It's almost impossible to truly enjoy the amount of work and dedication artists, songwriters, musicians and the like put into their music. With every song being instantly accessible, it's created a huge problem in the music industry where the supply far exceeds the demand and listeners are becoming bored with the music that's being released, since artists (mainly the music industry suits) force their artists to release music at such a rapid rate that the music itself sounds rushed.

There's a lack of emotional depth and connection needed for good music to connect with their listeners. The aim for this project is to bring back some sort of semblance of care for music. You are not just purchasing an album from the artist — you are purchasing their world, their brain, their perspective, and ultimately you're purchasing an incredible amount of time and work that goes into the music-making process.

The goal is to share the process, the depth, the emotions of your favorite artists, and reward them directly — as opposed to undermining their art on a massive platform that only cares about the numbers it's generating for their stakeholders.

## MVP user flow
1. User visits site, sees one LEA (album) for sale
2. User signs up / logs in
3. User clicks "Buy" → fake checkout (Stripe test mode later)
4. User now sees album in their Library
5. User clicks album → plays in custom web player
6. User interacts with liner notes, artist narrations, full listening experience

## Differentiating features (what streaming can't do)
- **Liner notes pages** — each track has its own page with lyrics, credits, artist commentary
- **Artist narrations** — exclusive audio commentary unlocked with purchase
- **Exclusive content** — bonus tracks, alternate versions, behind-the-scenes audio
- **Ownership-first UX** — your library, no algorithm, no recommendations

## Data model (rough)
- `users`: id, email, password_hash
- `albums`: id, title, artist, price_cents, cover_art_url
- `tracks`: id, album_id, title, track_number, audio_url, duration_seconds
- `purchases`: id, user_id, album_id, purchased_at, stripe_charge_id

## Tech stack
- Backend: Python + Flask
- Database (local): SQLite → migrate to PostgreSQL on RDS in Phase 4
- Frontend: HTML/CSS/JS + Jinja templates
- Audio: HTML5 `<audio>` element for MVP
- Payments: Stripe (test mode)
- Auth: Custom session-based (lifted from CS50 Finance pattern)
- Deployment: AWS (S3 + CloudFront + EC2 + RDS) — Phase 4

## NOT in scope for MVP
- Native desktop or mobile apps (web only)
- Multiple artists or self-serve artist onboarding (one hardcoded album)
- Streaming service integration (intentional — defeats the purpose)
- Real payments (Stripe test mode only)
- Social features (sharing, comments, etc.)

## What "done" means for CS50 submission
- All MVP flows working end-to-end
- Deployed live on AWS
- README ≈750 words
- 3-minute demo video
- Public GitHub repo with clean commit history