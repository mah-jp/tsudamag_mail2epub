#!/usr/bin/perl

# mail2epub.cgi
# by Masahiko OHKUBO <http://twitter.com/mah_jp>, <mah atmark remoteroom.jp>

use lib './extlib/lib/perl5';
use 5.8.0;
use strict;
use warnings;
use utf8;
use CGI;
use CGI::Carp qw(fatalsToBrowser);
use Color::Scheme;
use Config::Simple;
use EBook::EPUB;
use Encode;
use Encode::Guess qw(iso-2022-jp cp932 euc-jp);
use File::Temp qw(tempdir);
use GD;
use Path::Class;
use Unicode::EastAsianWidth;
use URI::Escape;

my %program = (
	name    => 'mail2epub.cgi',
	version => 'ver.20120404',
	url     => 'http://remoteroom.jp/mail2epub/'
);
my $configfile_magazine = 'magazine.ini';
my $magazine_type_default = 'default';
my $tmpdir_obj = File::Temp->newdir(CLEANUP => 1);
my $tmpdir = $tmpdir_obj->dirname;
my $config_magazine = new Config::Simple($configfile_magazine);

$CGI::POST_MAX = 2 * 1024 * 1024; # 1024KB
my $query = CGI->new;
my($body_1, $body_2, $body_3, $body_4, $body_5, $body_6, $body_7, $body_8) = ($query->param('body_1'), $query->param('body_2'), $query->param('body_3'), $query->param('body_4'), $query->param('body_5'), $query->param('body_6'), $query->param('body_7'), $query->param('body_8'));
$body_1 = Encode::decode('Guess', $body_1);
$body_1 =~ s/\x0D\x0A/\n/g;
$body_1 =~ tr/\x0D\x0A/\n\n/;
if ($body_2 ne '') {
	$body_2 = Encode::decode('Guess', $body_2);
	$body_2 =~ s/\x0D\x0A/\n/g;
	$body_2 =~ tr/\x0D\x0A/\n\n/;
}
if ($body_3 ne '') {
	$body_3 = Encode::decode('Guess', $body_3);
	$body_3 =~ s/\x0D\x0A/\n/g;
	$body_3 =~ tr/\x0D\x0A/\n\n/;
}
if ($body_4 ne '') {
	$body_4 = Encode::decode('Guess', $body_4);
	$body_4 =~ s/\x0D\x0A/\n/g;
	$body_4 =~ tr/\x0D\x0A/\n\n/;
}
if ($body_5 ne '') {
	$body_5 = Encode::decode('Guess', $body_5);
	$body_5 =~ s/\x0D\x0A/\n/g;
	$body_5 =~ tr/\x0D\x0A/\n\n/;
}
if ($body_6 ne '') {
	$body_6 = Encode::decode('Guess', $body_6);
	$body_6 =~ s/\x0D\x0A/\n/g;
	$body_6 =~ tr/\x0D\x0A/\n\n/;
}
if ($body_7 ne '') {
	$body_7 = Encode::decode('Guess', $body_7);
	$body_7 =~ s/\x0D\x0A/\n/g;
	$body_7 =~ tr/\x0D\x0A/\n\n/;
}
if ($body_8 ne '') {
	$body_8 = Encode::decode('Guess', $body_8);
	$body_8 =~ s/\x0D\x0A/\n/g;
	$body_8 =~ tr/\x0D\x0A/\n\n/;
}
my $config_target_default = $config_magazine->param(-block=>$magazine_type_default);
my $flag_tsuda = 0;
my $flag_cover = $query->param('cover');
my $flag_socialreading = $query->param('socialreading');
my $magazine_type = $query->param('type');
my $magazine_vol;
if ($magazine_type eq 'auto') {
	# vol.auto
	utf8::decode($$config_target_default{'body_key_regex'});
	my $body_key_regex = $$config_target_default{'body_key_regex'};
	if ($body_1 =~ /$body_key_regex/os) {
#		$magazine_type = 'tsuda_' . $1;
#		$magazine_vol = $1;
		$magazine_type = 'tsuda_' . $2 . $3;
		$magazine_vol = $2 . $3;
		$flag_tsuda = 1;
		$magazine_type =~ s/東北取材特別増刊号その/tohoku/;
	} else {
		$magazine_type = $magazine_type_default;
	}
}
my $config_target = $config_magazine->param(-block=>$magazine_type);
if ($magazine_type ne $magazine_type_default) {
	# set default
	my(%tmp_default) = %{$config_target_default};
	my $key;
	foreach $key (keys(%tmp_default)) {
		if (!defined($$config_target{$key})) {
			$$config_target{$key} = $tmp_default{$key};
		}
	}
}
# css
my($css_file, $css_str);
my %css_str = ( 'yoko_1' => 'y', 'yoko_2' => 'ym', 'tate_1' => 't', 'tate_2' => 'tm' );
if (defined($css_str{$query->param('css')})) {
	$css_file = $$config_target{'css_' . $query->param('css')};
	$css_str = $css_str{$query->param('css')};
} else {
	$css_file = $$config_target{'css_yoko_1'};
	$css_str = $css_str{'yoko_1'};
}
# main
my($packfile, $file) = &make_epub($tmpdir, $flag_tsuda, $flag_cover, $flag_socialreading, $magazine_vol, $config_target, $css_file, $css_str, \%program, $body_1, $body_2, $body_3, $body_4, $body_5, $body_6, $body_7, $body_8);
&download_epub($packfile, $file);
exit;

sub download_epub {
	my($packfile, $filename) = @_;
	printf('Content-Type: application/octed-stream' . "\n");
	printf('Content-Disposition: attachment; filename="%s"' . "\n", $filename);
	printf('Content-Length: %d' . "\n\n", -s($packfile));
	print scalar Path::Class::file($packfile)->slurp( iomode => '<:raw' );
	return;
}

sub make_epub {
	my($tmpdir, $flag_tsuda, $flag_cover, $flag_socialreading, $magazine_vol, $config_target, $css_file, $css_str, $ref_program, $body_1, $body_2, $body_3, $body_4, $body_5, $body_6, $body_7, $body_8) = @_;
	# body and toc
	my $body;
	if (defined($$config_target{'heading_line_regex'}) && ($$config_target{'heading_line_regex'} ne '')) {
		utf8::decode($$config_target{'heading_line_regex'});
		utf8::decode($$config_target{'heading_start_regex'});
		$body = $body_1 . "\n" . 
			&cut_header($body_2, $$config_target{'heading_start_regex'}, $$config_target{'heading_start_part2'}) . "\n" . 
			&cut_header($body_3, $$config_target{'heading_start_regex'}, $$config_target{'heading_start_part3'}) . "\n" . 
			&cut_header($body_4, $$config_target{'heading_start_regex'}, $$config_target{'heading_start_part4'}) . "\n" . 
			&cut_header($body_5, $$config_target{'heading_start_regex'}, $$config_target{'heading_start_part5'}) . "\n" . 
			&cut_header($body_6, $$config_target{'heading_start_regex'}, $$config_target{'heading_start_part6'}) . "\n" . 
			&cut_header($body_7, $$config_target{'heading_start_regex'}, $$config_target{'heading_start_part7'}) . "\n" . 
			&cut_header($body_8, $$config_target{'heading_start_regex'}, $$config_target{'heading_start_part8'});
	} else {
		$body = $body_1 . "\n" . $body_2 . "\n" . $body_3 . "\n" . $body_4 . "\n" . $body_5 . "\n" . $body_6 . "\n" . $body_7 . "\n" . $body_8;
	}
	my @body = split("\n", $body);
	my($ref_width, $maxwidth) = &get_width(\@body);
	if (defined($$config_target{'unfold_maxwidth'}) && ($$config_target{'unfold_maxwidth'} != 0)) {
		$maxwidth = $$config_target{'unfold_maxwidth'};
	}
	$body = &unfold_text(\@body, $ref_width, $maxwidth, $$config_target{'unfold_margin_minus'}, $$config_target{'unfold_margin_plus'});
	$body =~ s/"/&quot;/g;
	$body =~ s/</&lt;/g;
	$body =~ s/>/&gt;/g;
	$body =~ s/&/&amp;/g;
#	$body = &tagging_twitter($body);
#	$body = &tagging_link($body);
	my(@chapter, $ref_chapters, $ref_heading, $ref_toc, $toc);
	if (defined($$config_target{'heading_line_regex'}) && ($$config_target{'heading_line_regex'} ne '')) {
		($ref_chapters, $ref_heading, $ref_toc) = &split_chapter(\$body, $$config_target{'heading_line_regex'}, $$config_target{'heading_start_regex'}, $$config_target{'heading_start_part1'});
		$toc = '<ul><li>' . join('</li><li>', @$ref_toc) . '</li></ul>';
		my $ref_chapter = [ map { $_ } @$ref_chapters ];
		my @ref_chapter = @$ref_chapter;
		@chapter = map { join("\n", @$_) } @ref_chapter;
	} else {
		$chapter[0] = $body;
	}
	my($i);
	for ( $i = 0; $i < scalar(@chapter); $i++) {
		$chapter[$i] = &tagging_link(&tagging_twitter($chapter[$i]));
	}
	# endnote
	if (defined($$config_target{'endnote_regex'}) && ($$config_target{'endnote_regex'} ne '')) {
		utf8::decode($$config_target{'endnote_regex'});
		my $ref_chapter = &tagging_endnote(\@chapter, $$config_target{'endnote_regex'});
		@chapter = @$ref_chapter;
	}
#	# paragraph
#	if (defined($$config_target{'paragraph_yes_regex'}) && ($$config_target{'paragraph_yes_regex'} ne '')) {
#		utf8::decode($$config_target{'paragraph_yes_regex'});
#		utf8::decode($$config_target{'paragraph_no_regex'});
#		$body = &analyze_paragraph($ref_body, $$config_target{'paragraph_yes_regex'}, $$config_target{'paragraph_no_regex'});
#	} else {
#		$body = join('<br />' . "\n", @$ref_body);
#	}
	# attributes
	my @datetime = localtime();
	my $file = $$config_target{'filename_prefix'} . sprintf('%04d%02d%02d-%02d%02d_%s', $datetime[5] + 1900, $datetime[4] + 1, $datetime[3], $datetime[2], $datetime[1], $css_str) . '.epub';
	utf8::decode($$config_target{'title'});
	utf8::decode($$config_target{'title_1'});
	utf8::decode($$config_target{'title_2'});
	utf8::decode($$config_target{'title_3'});
	my($title, @title);
	$title = $$config_target{'title'};
	if ($flag_tsuda == 1) {
		@title = ($$config_target{'title_1'}, $$config_target{'title_2'}, $$config_target{'title_3'});
		$title = join('', @title);
	}
	my $language = $$config_target{'language'};
	my $epub = EBook::EPUB->new;
	$epub->add_title($title);
	$epub->add_language($language);
	$epub->add_identifier($$config_target{'identifier_value'}, $$config_target{'identifier_key'});
	$epub->add_date(sprintf('%04d-%02d-%02d', $datetime[5] + 1900, $datetime[4] + 1, $datetime[3]));
	$epub->add_description(sprintf('converted by %s %s %s', $$ref_program{'name'}, $$ref_program{'version'}, $$ref_program{'url'}));
	if (defined($$config_target{'author'}) && ($$config_target{'author'} ne '')) {
		utf8::decode($$config_target{'author'});
		$epub->add_author($$config_target{'author'});
	}
	# stylesheet
	my $tag_stylesheet = '';
	my $stylesheet_id;
	if($css_file) {
		$stylesheet_id = $epub->copy_stylesheet($css_file, 'default.css');
		$tag_stylesheet = '<link href="default.css" rel="stylesheet" />';
	}
	# navpoint
	my $playorder = 1;
	my($chapter_id, $navpoint);
	if (($flag_tsuda == 1) && ($flag_cover == 1)) {
		# cover
		my $cover_file = &make_cover($tmpdir, 'png', $magazine_vol, $$config_target{'author'}, @title);
		my $cover_id = $epub->copy_image(Path::Class::file($tmpdir, $cover_file), $cover_file);
		$epub->add_meta_item('cover', $cover_id);
		$chapter_id = $epub->add_xhtml('cover.xhtml', &make_xhtml($language, [$title], $tag_stylesheet, 0, [$magazine_vol], sprintf('<img src="%s" alt="%s" class="mail2epub-cover" />', $cover_file, $title)), linear => 'no');
		$navpoint = $epub->add_navpoint(
			label => '(cover)',
			id => $chapter_id,
			content => 'cover.xhtml',
			play_order => $playorder
		);
		$playorder++;
	}
	$chapter_id = $epub->add_xhtml('chapter_0.xhtml', &make_xhtml($language, [$title], $tag_stylesheet, $flag_socialreading, [$magazine_vol], $chapter[0], $toc));
	$navpoint = $epub->add_navpoint(
		label => $title,
		id => $chapter_id,
		content => 'chapter_0.xhtml',
		play_order => $playorder
	);
	$playorder++;
	if ($ref_heading) {
		my(@heading) = @$ref_heading;
		my $chapter_no = 1;
		while(@heading) {
			my($label, $name) = @{shift(@heading)};
			$chapter_id = $epub->add_xhtml(sprintf('chapter_%d.xhtml', $chapter_no), &make_xhtml($language, [$title, $label], $tag_stylesheet, $flag_socialreading, [$magazine_vol, $chapter_no], $chapter[$chapter_no]));
			$navpoint->add_navpoint(
				label => $label,
				id => $chapter_id,
				content => $name,
				play_order => $playorder
			);
			$playorder ++;
			$chapter_no ++;
		}
	}
	# pack
	my $packfile = Path::Class::file($tmpdir, $file);
	$epub->pack_zip("$packfile");
	return($packfile, $file);
}

sub make_xhtml {
	my($language, $ref_name, $tag_stylesheet, $flag_socialreading, $ref_position, $body, $toc) = @_;
	my($tag_toc, $result, $tag_socialreading, $tag_socialreading_short, $twitter_search, $twitter_write, $twitter_read);
	my($title) = $$ref_name[0];
	my($chapter_name) = $$ref_name[1];
	my($volume_no) = $$ref_position[0];
	my($chapter_no) = $$ref_position[1];
	my($hashtag_base) = 'tsudamag';
	if ($flag_socialreading) {
		if ($chapter_name ne '') {
			# chapter
			$twitter_search = &link_twitter('search', sprintf('#%s%d_%d', $hashtag_base, $volume_no, $chapter_no));
#			$twitter_write  = &link_twitter('write',  sprintf('#%s%d_%d #%s%d 【%s】について: ', $hashtag_base, $volume_no, $chapter_no, $hashtag_base, $volume_no, $chapter_name));
			$twitter_write  = &link_twitter('write',  sprintf('#%s%d_%d #%s 【%s】について：', $hashtag_base, $volume_no, $chapter_no, $hashtag_base, $chapter_name));
#			$twitter_read   = &link_twitter('read',   sprintf('#%s%d_%d #%s%d %s【%s】を読み終えました。', $hashtag_base, $volume_no, $chapter_no, $hashtag_base, $volume_no, $title, $chapter_name));
			$twitter_read   = &link_twitter('read',   sprintf('#%s%d_%d #%s %s【%s】を読了。', $hashtag_base, $volume_no, $chapter_no, $hashtag_base, $title, $chapter_name));
			$tag_socialreading = sprintf('<div class="mail2epub-socialreading">Chapter %s　<a href="%s" target="_blank">●Tweet</a>　<a href="%s" target="_blank">▼検索</a>　<a href="%s" target="_blank">■読了</a></div>', $chapter_name, $twitter_write, $twitter_search, $twitter_read);
			$tag_socialreading_short = sprintf('<div class="mail2epub-socialreading"><a href="%s" target="_blank">●Tweet</a>　<a href="%s" target="_blank">▼検索</a>　<a href="%s" target="_blank">■読了</a></div>', $twitter_write, $twitter_search, $twitter_read);
		} else {
			# top
#			$twitter_search = &link_twitter('search', sprintf('#%s%d', $hashtag_base, $volume_no));
			$twitter_search = &link_twitter('search', sprintf('#%s', $hashtag_base));
#			$twitter_write  = &link_twitter('write',  sprintf('#%s%d 【%s】について...', $hashtag_base, $volume_no, $title));
			$twitter_write  = &link_twitter('write',  sprintf('#%s 【%s】について：', $hashtag_base, $title));
#			$twitter_read   = &link_twitter('read',   sprintf('#%s%d 【%s】を読み終えました。', $hashtag_base, $volume_no, $title));
			$twitter_read   = &link_twitter('read',   sprintf('#%s 【%s】を読了。', $hashtag_base, $title));
			$tag_socialreading = sprintf('<div class="mail2epub-socialreading">Text %s　<a href="%s" target="_blank">●Tweet</a>　<a href="%s" target="_blank">▼検索</a>　<a href="%s" target="_blank">■読了</a></div>', $title, $twitter_write, $twitter_search, $twitter_read);
			$tag_socialreading_short = sprintf('<div class="mail2epub-socialreading"><a href="%s" target="_blank">●Tweet</a>　<a href="%s" target="_blank">▼検索</a>　<a href="%s" target="_blank">■読了</a></div>', $twitter_write, $twitter_search, $twitter_read);
		}
	}
	if ($toc) {
		$tag_toc = sprintf('<h1 id="mail2epub-toc">%s</h1><!-- tag_socialreading_short --><dl class="mail2epub-toc"><dt>Table of Contents:</dt><dd>%s</dd></dl><hr />', $title, $toc);
	}
	$body =~ s/\n/<br \/>\n/g;
	$result = <<"__XHTML__";
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="$language" xml:lang="$language">
<head>
<title>$title</title>
$tag_stylesheet
</head>
<body>
<div id="mail2epub-container">
$tag_toc
$body
$tag_socialreading
</div>
</body>
</html>
__XHTML__
	$result =~ s/<!-- tag_socialreading -->/$tag_socialreading/g;
	$result =~ s/<!-- tag_socialreading_short -->/$tag_socialreading_short/g;
	return($result);
}

sub link_twitter {
	my($command, $keyword) = @_;
	my($url);
	if ($command eq 'search') {
		$url = sprintf('http://twitter.com/search?q=%s', URI::Escape::uri_escape_utf8($keyword));
	} elsif ($command eq 'write') {
		$url = sprintf('http://twitter.com/share?text=%s', URI::Escape::uri_escape_utf8($keyword));
	} elsif ($command eq 'read') {
		$url = sprintf('http://twitter.com/share?text=%s', URI::Escape::uri_escape_utf8($keyword));
	} else {
		$url = 'http://twitter.com/';
	}
	return($url);
}

sub make_cover {
	my($tmpdir, $type, $magazine_vol, $author, @title) = @_;
	# custom-1
#	$title[2] =~ s/[^0-9a-zA-Z\.]//g;
	my @fontsize;
	if ($title[2] =~ /東北取材特別増刊号/) {
		@fontsize = (  24,  38,  26,  12);
	} else {
		@fontsize = (  24,  38,  72,  12);
	};
	my @string = (@title, $author);
	my $width    = 547;
	my $height   = 729;
	my @belt_y   = ($height * 0.18, $height * 0.60);
	my @string_y = ($height * 0.57, $height * 0.69, $height * 0.92, $height * 0.97);
	my @string_x = (  52,  52,  52,  52);
#	my @fontsize = (  24,  38,  72,  12);
	my $font ='fonts/TakaoPGothic.ttf';
	my $alpha = 110;
	my $stripe = 1000;
	# im, color
	my $im = new GD::Image($width, $height, 1);
	$im->interlaced('true');
	$im->alphaBlending(1);
	my $color_white = $im->colorAllocate(255,255,255);
	my $color_black = $im->colorAllocate(  0,  0,  0);
	my $colorscheme = Color::Scheme->new
		->from_hue($magazine_vol * (360 / 20))
		->scheme('triade') # mono, triade, tetrade, analogic
		->add_complement(1) # scheme( analogic ) only
		->distance(0.5) # scheme( triade, tetrade, analogic) only
		->variation('default') # default, pastel, soft, light, hard, pale
		->web_safe(0);
	my @colorlist = $colorscheme->colors();
	my($color_group, @color);
	$im->filledRectangle(0, 0, $width - 1, $height - 1, $color_white);
	for ($color_group = 0; $color_group < (scalar(@colorlist) / 4); $color_group ++) {
		my $hex_color_saturated = $colorlist[$color_group * 4 + 0];
		my $hex_color_darkened  = $colorlist[$color_group * 4 + 1];
		my $hex_color_pale      = $colorlist[$color_group * 4 + 2];
		my $hex_color_lesspale  = $colorlist[$color_group * 4 + 3];
		my $color_saturated = $im->colorAllocate(&convert_hex2dec($hex_color_saturated));
		my $color_darkened  = $im->colorAllocate(&convert_hex2dec($hex_color_darkened));
		my $color_pale      = $im->colorAllocate(&convert_hex2dec($hex_color_pale));
		my $color_lesspale  = $im->colorAllocate(&convert_hex2dec($hex_color_lesspale));
		my $color_saturated_alpha = $im->colorAllocateAlpha(&convert_hex2dec($hex_color_saturated), $alpha);
		my $color_darkened_alpha  = $im->colorAllocateAlpha(&convert_hex2dec($hex_color_darkened), $alpha);
		my $color_pale_alpha      = $im->colorAllocateAlpha(&convert_hex2dec($hex_color_pale), $alpha);
		my $color_lesspale_alpha  = $im->colorAllocateAlpha(&convert_hex2dec($hex_color_lesspale), $alpha);
		# custom-1
		@color = ($color_black, $color_black, $color_darkened, $color_lesspale);
		# pattern
		my($i, $x, $y);
		my @color_random = ($color_saturated_alpha, $color_darkened_alpha, $color_pale_alpha, $color_lesspale_alpha);
		for ( $i = 0; $i < $stripe; $i++) {
			$x = rand($width * 2) - $width;
			$y = rand($belt_y[1] - $belt_y[0]);
			$im->line($x, $belt_y[0] + $y, $x + $width - 1, $belt_y[0] + $y, $color_random[rand(scalar(@color_random))]);
		}
		$im->rectangle(0, 0, $width - 1, $height - 1, $color_darkened);
	}
	# string
	my($counter) = 0;
	while(@string) {
		my($string) = shift(@string);
		$im->stringFT($color_white, $font, $fontsize[$counter], 0, $string_x[$counter] - 1, $string_y[$counter] - 1, $string);
		$im->stringFT($color_white, $font, $fontsize[$counter], 0, $string_x[$counter] - 1, $string_y[$counter] + 1, $string);
		$im->stringFT($color_white, $font, $fontsize[$counter], 0, $string_x[$counter] + 1, $string_y[$counter] - 1, $string);
		$im->stringFT($color_white, $font, $fontsize[$counter], 0, $string_x[$counter] + 1, $string_y[$counter] + 1, $string);
		$im->stringFT($color[$counter], $font, $fontsize[$counter], 0, $string_x[$counter], $string_y[$counter], $string);
		$counter ++;
	}
	# output
	my ($binary, $file);
	if ($type eq 'jpg') {
		$binary = $im->jpeg;
		$file = 'cover.jpg';
	} else {
		$binary = $im->png;
		$file = 'cover.png';
	}
	my $fh = Path::Class::File->new($tmpdir, $file)->open( '>:raw' );
	print $fh $binary;
	return($file);
}

sub convert_hex2dec {
	my($hex) = @_;
	return(hex(substr($hex, 0, 2)), hex(substr($hex, 2, 2)), hex(substr($hex, 4, 2)));
}

sub unfold_text {
	my($ref_text, $ref_width, $maxwidth, $margin_minus, $margin_plus) = @_;
	my @text = @$ref_text;
	my @width = @$ref_width;
	my($line, $width, $result);
	while(@text) {
		$line = shift(@text);
		$width = shift(@width);
		if (!($line =~ /\p{InFullwidth}/)) {
			$result .= $line . "\n";
		} elsif (
					(($width >= ($maxwidth - $margin_minus)) && ($width <= ($maxwidth + $margin_plus))) && 
					((length($text[0]) > 0) && (&match_endlink($line) == 0) && (&match_endlink($text[0]) == 0))
				) {
			$result .= $line;
		} else {
			$result .= $line . "\n";
		}
	}
	return($result);
}

# thanks: http://www.din.or.jp/~ohzaki/perl.htm#URI
sub match_endlink {
	my($text) = @_;
	if ($text =~ /s?https?:\/\/[-_.!~*'()a-zA-Z0-9;\/?:\@&=+\$,%#]+$/) {
		return(1);
	} else {
		return(0);
	}
}

#sub analyze_paragraph {
#	my($ref_text, $regex_yes, $regex_no) = @_;
#	my @text = @$ref_text;
#	my($line, @buffer, $buffer, $result);
#	while(@text) {
#		$buffer = '';
#		@buffer = ();
#		$line = shift(@text);
#		push(@buffer, $line);
#		$buffer .= $line;
#		while((@text) && ($line ne '')) {
#			$line = shift(@text);
#			push(@buffer, $line);
#			$buffer .= $line;
#		}
#		if (defined($regex_no) && ($regex_no ne '')) {
#			if (($buffer =~ /$regex_yes/o) && ($buffer !~ /$regex_no/o)) {
#				$result .= sprintf('<p>%s</p>' . "\n\n", $buffer);
#			} else {
#				$result .= join('<br />' . "\n", @buffer) . "\n";
#			}
#		} elsif ($buffer =~ /$regex_yes/o) {
#			$result .= sprintf('<p>%s</p>' . "\n\n", $buffer);
#		} else {
#			$result .= join('<br />' . "\n", @buffer) . "\n";
#		}
#	}
#	return($result);
#}

sub tagging_twitter {
	my($text) = @_;
	my($twitter_regex) = '([^0-9a-zA-Z_])\@([0-9a-zA-Z_]{1,15})';
	$text =~ s|$twitter_regex|$1<a href="http://twitter.com/$2" class="mail2epub-twitter">\@$2</a>|g;
	return($text);
}

sub split_chapter {
	my($ref_text, $heading_line_regex, $heading_start_regex, $heading_start_part) = @_;
	my @text = split("\n", $$ref_text);
	my($i, $line, $name, @result, @toc, @chapter);
	my($scanning) = 0;
	my($part) = 0;
	my($chapter_no) = 0;
	my($chapter_line) = 0;
	if (!defined($heading_start_regex) || ($heading_start_regex eq '')) {
		$scanning = 1;
	}
	for ($i = 0; $i < scalar(@text); $i++) {
		$line = $text[$i];
		if ($scanning == 1) {
			if (($line =~ /$heading_line_regex/o) && ($text[$i - 1] eq '')) {
				$chapter_no ++;
				$chapter_line = 0;
				$name = sprintf('mail2epub-line%d', $i + 1); # id
				$chapter[$chapter_no][$chapter_line] = sprintf('<h1 id="%s"><a href="%s">%s</a></h1><!-- tag_socialreading_short -->', $name, 'chapter_0.xhtml', $line);
				push(@result, [ $line, sprintf('chapter_%d.xhtml', $chapter_no) ]);
				push(@toc, sprintf('<a href="chapter_%d.xhtml">%s</a>', $chapter_no, $line));
			} else {
				$chapter[$chapter_no][$chapter_line] = $line;
			}
		} elsif ($line =~ /$heading_start_regex/o) {
			$part ++;
			if ($part >= $heading_start_part) {
				$scanning = 1;
			}
			$chapter[$chapter_no][$chapter_line] = $line;
		} else {
			$chapter[$chapter_no][$chapter_line] = $line;
		}
		$chapter_line ++;
	}
	return(\@chapter, \@result, \@toc);
}

sub tagging_endnote {
	my($ref_chapter, $endnote_regex) = @_;
	my(@before) = @$ref_chapter;
	my(@after, @text, $i ,$j, $endnote_key, $endnote_key_quotemeta, $id_note, $id_symbol);
	my($chapter_no) = 0;
	while(@before) {
		@text = split("\n", shift(@before));
		for ($i = scalar(@text) - 1; $i >= 0; $i--) {
			if ($text[$i] =~ /$endnote_regex/o ) {
				$endnote_key = $1;
				$endnote_key_quotemeta = quotemeta($1);
				$id_note = sprintf('mail2epub-endnote-note%d-%d', $chapter_no, $i);
				for ($j = $i - 1; $j >= 0; $j--) {
					if ($text[$j] =~ /$endnote_key_quotemeta/ ) {
						$id_symbol = sprintf('mail2epub-endnote-symbol%d-%d-%d', $chapter_no, $j, $i);
						$text[$j] =~ s|$endnote_key_quotemeta|<a href="#$id_note" id="$id_symbol" class="mail2epub-endnote-symbol">$endnote_key</a>|g;
					}
				}
				$text[$i] =~ s|$endnote_key_quotemeta|<a href="#$id_symbol" id="$id_note" class="mail2epub-endnote-note">$endnote_key</a>|;
			}
		}
		$chapter_no ++;
		push(@after, join("\n", @text));
	}
	return(\@after)
}

sub cut_header {
	my($text, $heading_start_regex, $heading_start_part) = @_;
	my @text = split("\n", $text);
	my($i, $line, @result);
	my($cutting) = 1;
	my($part) = 0;
	if (!defined($heading_start_regex) || ($heading_start_regex eq '')) {
		$cutting = 0;
	}
	for ($i = 0; $i < scalar(@text); $i++) {
		$line = $text[$i];
		if (($cutting == 1) && ($line =~ /$heading_start_regex/o)) {
			$part++;
			if ($part >= $heading_start_part) {
				$cutting = 0;
			}
		}
		if ($cutting == 0) {
			push(@result, $line);
		}
	}
	return(join("\n", @result));
}

# thanks: http://d.hatena.ne.jp/syohex/20110529/1306676606
sub get_width {
	my($ref_text) = @_;
	my @text = @$ref_text;
	my($line, $count, @width);
	my $maxwidth = 0;
	while(@text) {
		$line = shift(@text);
		$count = 0;
		while ($line =~ m{(?:(\p{InFullwidth})|(\p{InHalfwidth}))}g) {
			if (defined $1) {
				$count += 2;
			} else {
				$count += 1;
				# temporary patch: not ascii...
				if ($2 !~ m{[\x00-\xFF]}) {
					$count += 1;
				}
			}
		}
		push(@width, $count);
		if ((!($line =~ /\p{InHalfwidth}/)) && ($maxwidth < $count)) {
			$maxwidth = $count;
		}
	}
	return(\@width, $maxwidth);
}

# thanks: http://www.din.or.jp/~ohzaki/perl.htm#AutoLink
sub tagging_link {
	my($str) = @_;
	my($http_URL_regex, $ftp_URL_regex, $mail_regex, $tag_regex_, $comment_tag_regex, $tag_regex);
	my($text_regex, $result, $skip, $text_tmp, $tag_tmp);
	$http_URL_regex =
	q{\b(?:https?|shttp)://(?:(?:[-_.!~*'()a-zA-Z0-9;:&=+$,]|%[0-9A-Fa-f} .
	q{][0-9A-Fa-f])*@)?(?:(?:[a-zA-Z0-9](?:[-a-zA-Z0-9]*[a-zA-Z0-9])?\.)} .
	q{*[a-zA-Z](?:[-a-zA-Z0-9]*[a-zA-Z0-9])?\.?|[0-9]+\.[0-9]+\.[0-9]+\.} .
	q{[0-9]+)(?::[0-9]*)?(?:/(?:[-_.!~*'()a-zA-Z0-9:@&=+$,]|%[0-9A-Fa-f]} .
	q{[0-9A-Fa-f])*(?:;(?:[-_.!~*'()a-zA-Z0-9:@&=+$,]|%[0-9A-Fa-f][0-9A-} .
	q{Fa-f])*)*(?:/(?:[-_.!~*'()a-zA-Z0-9:@&=+$,]|%[0-9A-Fa-f][0-9A-Fa-f} .
	q{])*(?:;(?:[-_.!~*'()a-zA-Z0-9:@&=+$,]|%[0-9A-Fa-f][0-9A-Fa-f])*)*)} .
	q{*)?(?:\?(?:[-_.!~*'()a-zA-Z0-9;/?:@&=+$,]|%[0-9A-Fa-f][0-9A-Fa-f])} .
	q{*)?(?:#(?:[-_.!~*'()a-zA-Z0-9;/?:@&=+$,]|%[0-9A-Fa-f][0-9A-Fa-f])*} .
	q{)?};
	$ftp_URL_regex =
	q{\bftp://(?:(?:[-_.!~*'()a-zA-Z0-9;&=+$,]|%[0-9A-Fa-f][0-9A-Fa-f])*} .
	q{(?::(?:[-_.!~*'()a-zA-Z0-9;&=+$,]|%[0-9A-Fa-f][0-9A-Fa-f])*)?@)?(?} .
	q{:(?:[a-zA-Z0-9](?:[-a-zA-Z0-9]*[a-zA-Z0-9])?\.)*[a-zA-Z](?:[-a-zA-} .
	q{Z0-9]*[a-zA-Z0-9])?\.?|[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)(?::[0-9]*)?} .
	q{(?:/(?:[-_.!~*'()a-zA-Z0-9:@&=+$,]|%[0-9A-Fa-f][0-9A-Fa-f])*(?:/(?} .
	q{:[-_.!~*'()a-zA-Z0-9:@&=+$,]|%[0-9A-Fa-f][0-9A-Fa-f])*)*(?:;type=[} .
	q{AIDaid])?)?(?:\?(?:[-_.!~*'()a-zA-Z0-9;/?:@&=+$,]|%[0-9A-Fa-f][0-9} .
	q{A-Fa-f])*)?(?:#(?:[-_.!~*'()a-zA-Z0-9;/?:@&=+$,]|%[0-9A-Fa-f][0-9A} .
	q{-Fa-f])*)?};
	$mail_regex =
	q{(?:[-!#-'*+/-9=?A-Z^-~]+(?:\.[-!#-'*+/-9=?A-Z^-~]+)*|"(?:[!#-\[\]-} .
	q{~]|\\\\[\x09 -~])*")@[-!#-'*+/-9=?A-Z^-~]+(?:\.[-!#-'*+/-9=?A-Z^-~]+} .
	q{)*};
	$tag_regex_ = q{[^"'<>]*(?:"[^"]*"[^"'<>]*|'[^']*'[^"'<>]*)*(?:>|(?=<)|$(?!\n))}; #'}}}}
	$comment_tag_regex =
		'<!(?:--[^-]*-(?:[^-]+-)*?-(?:[^>-]*(?:-[^>-]+)*?)??)*(?:>|$(?!\n)|--.*$)';
	$tag_regex = qq{$comment_tag_regex|<$tag_regex_};
	$text_regex = q{[^<]*};
	$result = ''; $skip = 0;
	while ($str =~ /($text_regex)($tag_regex)?/gso) {
#		last if ($1 eq '' and $2 eq '');
		last if (!defined($1) and !defined($2));
		$text_tmp = $1;
		$tag_tmp = $2;
		if ($skip) {
			$result .= $text_tmp . $tag_tmp;
			$skip = 0 if $tag_tmp =~ /^<\/[aA](?![0-9A-Za-z])/;
		} else {
#			$text_tmp =~ s{($http_URL_regex|$ftp_URL_regex|($mail_regex))}
#				{my($org, $mail) = ($1, $2);
#					(my $tmp = $org) =~ s/"/&quot;/g;
#					'<a href="' . ($mail ne '' ? 'mailto:' : '') . "$tmp\">$org</a>"}ego;
			$text_tmp =~ s{($http_URL_regex|$ftp_URL_regex|($mail_regex))}
				{my($org, $mail) = ($1, $2);
					(my $tmp = $org) =~ s/"/&quot;/g;
					'<a href="' . (defined($mail) ? 'mailto:' : '') . $tmp . '" class="' . (defined($mail) ? 'mail2epub-mailto' : 'mail2epub-link') . '">' . $org . '</a>'}ego;
#			$result .= $text_tmp . $tag_tmp;
#			$skip = 1 if $tag_tmp =~ /^<[aA](?![0-9A-Za-z])/;
#			if ($tag_tmp =~ /^<(XMP|PLAINTEXT|SCRIPT)(?![0-9A-Za-z])/i) {
#				$str =~ /(.*?(?:<\/$1(?![0-9A-Za-z])$tag_regex_|$))/gsi;
#				$result .= $1;
#			}
			if (defined($tag_tmp)) {
				$result .= $text_tmp . $tag_tmp;
				$skip = 1 if $tag_tmp =~ /^<[aA](?![0-9A-Za-z])/;
				if ($tag_tmp =~ /^<(XMP|PLAINTEXT|SCRIPT)(?![0-9A-Za-z])/i) {
					$str =~ /(.*?(?:<\/$1(?![0-9A-Za-z])$tag_regex_|$))/gsi;
					$result .= $1;
				}
			} else {
				$result .= $text_tmp;
			}
		}
	}
	return($result);
}
