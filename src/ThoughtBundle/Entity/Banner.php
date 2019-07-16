<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 09.07.19
 * Time: 12:33
 */

namespace ThoughtBundle\Entity;

use Doctrine\ORM\Mapping as ORM;

/**
 * Class Banner
 * @package ThoughtBundle\Entity
 *
 * @ORM\Table(name="banners")
 * @ORM\Entity()
 */
class Banner
{
    /**
     * @var int
     *
     * @ORM\Id
     * @ORM\Column(type="integer")
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    protected $id;

    /**
     * @var string
     * @ORM\Column(type="string", nullable=true)
     */
    protected $title;

    /**
     * @var string
     * @ORM\Column(type="text")
     */
    protected $content;

    /**
     * @var DynamicPage
     *
     * @ORM\ManyToOne(targetEntity="ThoughtBundle\Entity\DynamicPage", inversedBy="banners")
     * @ORM\JoinColumn(name="page_id", referencedColumnName="id")
     */
    protected $page;

    /**
     * @var boolean
     *
     * @ORM\Column(type="boolean")
     */
    protected $isActive = false;

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
     * @return Banner
     */
    public function setTitle($title)
    {
        $this->title = $title;
        return $this;
    }

    /**
     * @return string
     */
    public function getContent()
    {
        return $this->content;
    }

    /**
     * @param string $content
     * @return Banner
     */
    public function setContent($content)
    {
        $this->content = $content;
        return $this;
    }

    /**
     * @return DynamicPage
     */
    public function getPage()
    {
        return $this->page;
    }

    /**
     * @param DynamicPage $page
     * @return Banner
     */
    public function setPage($page)
    {
        $this->page = $page;
        return $this;
    }

    /**
     * @return bool
     */
    public function isActive()
    {
        return $this->isActive;
    }

    /**
     * @param bool $isActive
     * @return Banner
     */
    public function setIsActive($isActive)
    {
        $this->isActive = $isActive;
        return $this;
    }
}