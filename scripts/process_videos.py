import os
import subprocess
import json
from loguru import logger as lg


class VideoProcessor:
    def __init__(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.input_dir = os.path.join(self.base_dir, "input")
        self.audio_path = os.path.join(self.base_dir, "input/source.mp3")
        self.output_dir = os.path.join(self.base_dir, "output", "processed_videos")
        self.output_dir_transition = os.path.join(self.base_dir, "output", "transition_video")
        self.config_file = os.path.join(self.base_dir, "config", "video_config.json")
        self.final_output = os.path.join(self.output_dir, "final.mp4")

        os.makedirs(self.output_dir, exist_ok=True)

        with open(self.config_file, "r") as f:
            self.video_configs = json.load(f)

    def process_video(self, input_file, output_file, subtitle_text=None, animation=None):
        """Applies resolution normalization and subtitles in a single step."""
        # Base video filters: Normalize resolution and frame rate
        filters = [
            "scale=1920:2688:force_original_aspect_ratio=decrease,pad=1920:2688:(ow-iw)/2:(oh-ih)/2",
            "fps=20",
            "format=yuv420p"
        ]

        # Combine all filters
        filter_chain = ",".join(filters)

        command = [
            "ffmpeg", "-y", "-i", input_file,
            "-vf", filter_chain,
            "-c:v", "libx264", "-crf", "18", "-preset", "ultrafast",
            "-an",
            output_file
        ]

        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            lg.error(f"Error processing {input_file}: {e}")

    def process_all_videos(self):
        processed_videos = []
        for file in sorted(os.listdir(self.input_dir)):
            if file.endswith(".mp4"):
                input_path = os.path.join(self.input_dir, file)
                output_path = os.path.join(self.output_dir, file)  # Directly store final output

                self.process_video(input_path, output_path)
                processed_videos.append(output_path)

        lg.info("All videos processed successfully!")
        self.video_effect(processed_videos)

    def video_effect(self, video_list):
        for idx, video in enumerate(video_list):
            video_name = os.path.basename(video)
            output_video_path = os.path.join(self.output_dir_transition, video_name)
            if video_name == "1.mp4":
                # Step 1: Add zoom effect at the start
                step1_output = "temp_step1.mp4"
                subprocess.run([
                    "ffmpeg", "-y", "-i", video,
                    "-vf", "zoompan=z='if(lt(in_time,0), 2, 2-(40*(in_time-0.5)))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1,scale=1920:2688,setpts=N/20/TB",
                    "-r", "20", "-pix_fmt", "yuv420p", "-crf", "28", "-preset", "ultrafast", step1_output
                ])
                
                # Step 2: Add white screen with crossfade at the start
                step2_output = "temp_step2.mp4"
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-t", "1.1", "-i", "color=c=white:s=1920x2688:rate=20",
                    "-i", step1_output, "-filter_complex",
                    "[0:v]format=pix_fmts=yuv420p,settb=1/10240,setpts=PTS-STARTPTS[white];"
                    "[1:v]settb=1/10240,setpts=PTS-STARTPTS[video];"
                    "[white][video]xfade=transition=fade:duration=1:offset=0.5",
                    "-pix_fmt", "yuv420p", "-crf", "28", "-preset", "ultrafast", step2_output
                ])
                
                # Step 3: Apply zoom effect at the end
                step3_output = "temp_step3.mp4"
                subprocess.run([
                    "ffmpeg", "-y", "-i", step2_output,
                    "-vf", "zoompan=z='if(lt(in_time,4.8),1,1+((in_time-4.8)*10))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1,scale=1920:2688,setsar=1,setpts=N/20/TB",
                    "-r", "20", "-pix_fmt", "yuv420p", "-crf", "28", "-preset", "ultrafast", step3_output
                ])
                
                # Step 4: Apply white screen with crossfade at the end
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-t", "1.1", "-i", "color=c=white:s=1920x2688:rate=20",
                    "-i", step3_output, "-filter_complex",
                    "[0:v]format=pix_fmts=yuv420p,settb=1/10240,setpts=PTS-STARTPTS[white];"
                    "[1:v]settb=1/10240,setpts=PTS-STARTPTS[video];"
                    "[video][white]xfade=transition=fade:duration=1:offset=4.5",
                    "-pix_fmt", "yuv420p", "-crf", "28", "-preset", "ultrafast", output_video_path
                ])
                
                # Clean up intermediate files
                os.remove(step1_output)
                os.remove(step2_output)
                os.remove(step3_output)

            elif video_name == "8.mp4":
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-t", "1.1", "-i", "color=c=white:s=1920x2688:rate=20",
                    "-i", video, "-filter_complex",
                    "[0:v]format=pix_fmts=yuv420p,settb=1/10240,setpts=PTS-STARTPTS[white];"
                    "[1:v]settb=1/10240,setpts=PTS-STARTPTS[video];"
                    "[video][white]xfade=transition=fade:duration=1:offset=7.5",  
                    "-pix_fmt", "yuv420p", "-crf", "28", "-preset", "ultrafast", output_video_path
                ])

            else:
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-t", "1.1", "-i", "color=c=white:s=1920x2688:rate=20",
                    "-i", video, "-filter_complex",
                    "[0:v]format=pix_fmts=yuv420p,settb=1/10240,setpts=PTS-STARTPTS[white];"
                    "[1:v]settb=1/10240,setpts=PTS-STARTPTS[video];"
                    "[video][white]xfade=transition=fade:duration=1:offset=4.5",
                    "-pix_fmt", "yuv420p", "-crf", "28", "-preset", "ultrafast", output_video_path
                ])
        self.concatenate_videos()
            

    def concatenate_videos(self):
        input_dir = os.path.join("output", "transition_video")
        temp_output = "temp_video.mp4"  # Intermediate file
        final_output = "final_video.mp4"  # Final video with subtitles
        
        video_files = [os.path.join(input_dir, f"{i}.mp4") for i in range(1, 9)]
        
        # Construct the ffmpeg command
        ffmpeg_command = ["ffmpeg", "-y"]
        
        # Add input files
        for video in video_files:
            ffmpeg_command.extend(["-i", video])
        
        ffmpeg_command.extend(["-i", self.audio_path])

        # Create the filter_complex string with crossfade transitions
        filter_complex = ""
        for i in range(7):  # Since there are 8 videos, we need 7 transitions
            offset = (i + 1) * 5.5  # Adjust offset as per your requirement
            if i == 0:
                filter_complex += f"[0:v][1:v]xfade=transition=fade:duration=1:offset={offset}[v0]; "
            else:
                filter_complex += f"[v{i-1}][{i+1}:v]xfade=transition=fade:duration=1:offset={offset}[v{i}]; "
        
        # Remove trailing space and semicolon
        filter_complex = filter_complex.strip("; ")
        
        # Append filter_complex and mapping to the command
        ffmpeg_command.extend([
            "-filter_complex", filter_complex,
            "-map", "[v6]",  # Final video output stream
            "-map", "8:a",  # Map audio stream (last input)
            "-c:v", "libx264", "-crf", "28", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-ac", "2",
            "-async", "1",
            "-c:a", "aac", "-b:a", "192k",  # Encode audio
            "-shortest",  # Trim audio if it's longer than video
            temp_output  # Save intermediate file
        ])
        
        # Run the first ffmpeg command (concatenation)
        subprocess.run(ffmpeg_command, check=True)
        
        # Add subtitles to the concatenated video
        ffmpeg_subtitle_command = [
            "ffmpeg", "-y",
            "-i", temp_output,
            "-vf", "ass=final.ass",
            "-c:v", "libx264", "-crf", "28", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            final_output
        ]
        
        # Run the second ffmpeg command (adding subtitles)
        subprocess.run(ffmpeg_subtitle_command, check=True)
        
        print(f"Final video saved as {final_output}")



if __name__ == "__main__":
    processor = VideoProcessor()
    processor.process_all_videos()
