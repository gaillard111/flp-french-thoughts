<?php

namespace ThoughtBundle\Entity;

use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\ORM\Mapping as ORM;
use Gedmo\Mapping\Annotation as Gedmo;

/**
 * @ORM\Table(name="dynamic_pages")
 * @ORM\Entity()
 */
class DynamicPage
{
    /**
     * @var int
     *
     * @ORM\Column(name="id", type="integer")
     * @ORM\Id
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    private $id;

    /**
     * @var string
     *
     * @ORM\Column(type="string")
     */
    private $title;

    /**
     * @var string
     *
     * @ORM\Column(type="text")
     */
    private $text;

    /**
     * @var string
     *
     * @ORM\Column(type="string")
     *
     * @Gedmo\Slug(fields={"title"}, updatable=false, separator="_")
     */
    private $slug;

    /**
     * @var ArrayCollection|Banner[]
     *
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\Banner", mappedBy="page")
     */
    private $banners;

    /**
     * @return int
     */
    public function getId()
    {
        return $this->id;
    }

    /**
     * @return string
     */
    public function getTitle()
    {
        return $this->title;
    }

    /**
     * @param string $title
     *
     * @return DynamicPage
     */
    public function setTitle($title)
    {
        $this->title = $title;
        return $this;
    }

    /**
     * @return string
     */
    public function getText()
    {
        return $this->text;
    }

    /**
     * @param string $text
     *
     * @return DynamicPage
     */
    public function setText($text)
    {
        $this->text = $text;
        return $this;
    }

    /**
     * @return string
     */
    public function getSlug()
    {
        return $this->slug;
    }

    /**
     * @param string $slug
     *
     * @return DynamicPage
     */
    public function setSlug($slug)
    {
        $this->slug = $slug;
        return $this;
    }

    /**
     * @return ArrayCollection|Banner[]
     */
    public function getBanners()
    {
        return $this->banners;
    }

    /**
     * @param ArrayCollection|Banner[] $banners
     *
     * @return DynamicPage
     */
    public function setBanners($banners)
    {
        $this->banners = $banners;
        return $this;
    }
}